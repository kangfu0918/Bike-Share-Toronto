# -*- coding: utf-8 -*-
"""EY Bike Share Toronto.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ttTfsJOVAbUvaw5HRJuZWiFi0ofRGfx1
"""

# Install required library package
!pip install category_encoders

# Import the required libraries
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
import pandas as pd
import numpy as np
import glob
import os
from sklearn.model_selection import train_test_split
import re
import calendar
#from datetime import datetime
import datetime as dt
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_curve, roc_auc_score
#import category_encoders as ce
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn import metrics
from sklearn.preprocessing import StandardScaler, KBinsDiscretizer, FunctionTransformer, OneHotEncoder
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
import seaborn as sns

from google.colab import drive
drive.mount('/content/gdrive')

# Data Path (Bike Share and Weather)
path1 = '/content/gdrive/MyDrive/EY Toronto Bike Share/Data/Bike Share Data/2022'
path2 = '/content/gdrive/MyDrive/EY Toronto Bike Share/Data/Bike Share Data/2021'
path3 = '/content/gdrive/MyDrive/EY Toronto Bike Share/Data/Bike Share Data/2020'
path_weather = '/content/gdrive/MyDrive/EY Toronto Bike Share/Data/Weather Data/weatherstats_toronto_daily.csv'

# Load 2022 data
all_files = glob.glob(os.path.join(path1, "*.csv"))     # advisable to use os.path.join as this makes concatenation OS independent

print (all_files)
df_from_each_file = (pd.read_csv(f,encoding='cp1252') for f in all_files)
df2022= pd.concat(df_from_each_file, ignore_index=True)
df2022.head(10)

# Remove the special characters of the feature name
df2022=df2022.rename(columns={"ï»¿Trip Id": "Trip Id"})

df2022.info()

# Load 2021 data
all_files = glob.glob(os.path.join(path2, "*.csv"))     # advisable to use os.path.join as this makes concatenation OS independent

print (all_files)
df_from_each_file = (pd.read_csv(f,encoding='cp1252') for f in all_files)
df2021= pd.concat(df_from_each_file, ignore_index=True)
df2021.head(10)

# Remove extra trip id column
df2021_1=df2021[df2021['ï»¿Trip Id'].isna()]
df2021_1=df2021_1.drop(columns=['ï»¿Trip Id'])
df2021_1.head()

df2021_2=df2021[df2021['Trip Id'].isna()]
df2021_2=df2021_2.drop(columns=['Trip Id'])
df2021_2=df2021_2.rename(columns={"ï»¿Trip Id": "Trip Id"})
df2021_2.head()
df2021=pd.concat([df2021_1,df2021_2])

# df2021 dataset information
df2021.info()

# Load 2020 data
all_files = glob.glob(os.path.join(path3, "*.csv"))     # advisable to use os.path.join as this makes concatenation OS independent

print (all_files)
df_from_each_file = (pd.read_csv(f,encoding='cp1252') for f in all_files)
df2020= pd.concat(df_from_each_file, ignore_index=True)
df2020.head(10)

# Remove the special characters of the feature name
df2020=df2020.rename(columns={"ï»¿Trip Id": "Trip Id"})

# df2020.info()

# Concatenate 2022, 2021, 2020 data 
df=pd.concat([df2022,df2021,df2020])

df.head(10)

df.info()

# Load Weather data 
weather_df = pd.read_csv(path_weather, usecols=['date', 'avg_temperature', 'avg_relative_humidity', 'avg_wind_speed','min_windchill', 'rain', 'snow' ], parse_dates=['date'])

weather_df.head()

# Create a new feature showing the date
weather_df['date_only'] = weather_df['date'].dt.date
weather_df.info()

"""# Feature Engineering """

# Look for bad date columns
df[df['Start Time'].str.contains('\d{1,2}/\d{1,2}/\d{2}(?:\d{2})? \d{1,2}:\d{1,2}') == False]

# Drop all NaN rows then check df
df.dropna(inplace=True)
df[df.isna().any(axis=1)]

df.info()

# Copy to a new dataframe
data_df = df.copy()

# Drop data rows that have invalid date formats (249 were detected above)
data_df = data_df[data_df['Start Time'].str.contains('\d{1,2}/\d{1,2}/\d{2}(?:\d{2})? \d{1,2}:\d{1,2}') == True]

# Convert columns to date/time
data_df['Start Time']= pd.to_datetime(data_df['Start Time'])
data_df['End Time']= pd.to_datetime(data_df['End Time'])
data_df['date_only'] = data_df['Start Time'].dt.date
data_df.info()

# Convert station ids to ints
data_df[["Trip Id", "Start Station Id", "End Station Id"]] = data_df[["Trip Id", "Start Station Id", "End Station Id"]].apply(pd.to_numeric)
data_df.info()

# Add in flag to indicate if a trip was one-way
data_df['one_way_trip'] = df['Start Station Id'] == df['End Station Id']
data_df['one_way_trip'] = data_df['one_way_trip'].map(lambda x : 'No' if x else 'Yes')

# Add features for Month name, day_name and Hour of the day
data_df['month'] = data_df['Start Time'].map(lambda x : calendar.month_abbr[x.month])
data_df['day_name'] = data_df['Start Time'].map(lambda x : calendar.day_name[x.weekday()])
data_df['hour'] = data_df['Start Time'].dt.hour
data_df['year'] = data_df['Start Time'].dt.year

# Create bins for time of day, use 3 hour segments
bins = [0, 3, 6, 9, 12, 15, 18, 21, 24]
bin_labels = ['0-3','3-6', '6-9', '9-12', '12-15', '15-18', '18-21', '21-23']
data_df["hour-bin"] = pd.cut(data_df["hour"], bins, right=False,  include_lowest=True, labels = bin_labels).astype(str)

# See how many rides fall into each 
trip_bins = [0, 5, 15, 25, 45, 90, 100000]
trip_bin_labels = ['0-5','5-15', '15-25', '25-45', '45-90', '90+']

buckets = pd.cut(data_df["Trip  Duration"]/60,  trip_bins, 
                 include_lowest=True,
                 right=False, labels = trip_bin_labels)
def get_stats(group):
    return {
        'count': group.count(),
        'min': group.min(),
        'max': group.max(),
        'mean': group.mean(),
    }

grouped = data_df["Trip  Duration"].groupby(buckets)
grouped.apply(get_stats).unstack

# Create bins for the Trip duration in mins
data_df["duration-min"] = pd.cut(data_df["Trip  Duration"]/60,  trip_bins, right=True, include_lowest=True, labels = trip_bin_labels).astype(str)

data_df["duration-min"].unique()

data_df["hour-bin"].unique()

# Check there are no nan buckets which indicates the range does not cover all values
data_df[data_df["duration-min"]=='nan']

# Merge with the weather data
data_df = data_df.merge(weather_df, on='date_only', how='left')

# fill all the NA with 0
data_df.fillna(value=0, inplace=True)
data_df[data_df.isna().any(axis=1)]

data_df.info()
data_df.describe()

data_df[300:310]

"""# Exploratory Analysis """

# data separated by year
data_df2020=data_df[data_df['year']==2020]
data_df2021=data_df[data_df['year']==2021]
data_df2022=data_df[data_df['year']==2022]

#Bike Share Toronto membership 2020 
order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ax = sns.countplot(data=data_df2020, x='month', hue='User Type', palette='hls', order=order)
ax.tick_params(labelsize=12)
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)
ax.set_xlabel('Start Month')

ax.set_ylabel('Trip Count')

plt.title('Bike Share Toronto Ridership 2020',fontsize=14)
plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0.)

# Bike Share Toronto membership 2021 
order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ax = sns.countplot(data=data_df2021, x='month', hue='User Type', palette='hls', order=order)
ax.tick_params(labelsize=12)
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)
ax.set_xlabel('Start Month')

ax.set_ylabel('Trip Count')

plt.title('Bike Share Toronto Ridership 2021',fontsize=14)
plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0.)

# Bike Share Toronto membership 2022 
order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ax = sns.countplot(data=data_df2022, x='month', hue='User Type', hue_order=['Annual Member','Casual Member'], palette='hls', order=order)
ax.tick_params(labelsize=12)
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)
ax.set_xlabel('Start Month')

ax.set_ylabel('Trip Count')

plt.title('Bike Share Toronto Ridership 2022',fontsize=14)
plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0.)

# Bike Share Toronto membership 2022 
order = [2020,2021,2022]

plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ax = sns.countplot(data=data_df, x='year', hue='User Type', palette='hls', order=order)
ax.tick_params(labelsize=12)
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)
ax.set_xlabel('Year')

ax.set_ylabel('Trip Count (million)')

plt.title('Bike Share Toronto Ridership 2020-2022',fontsize=14)
plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0.)

# Bike Share Toronto Ridership per day:
order=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ridership = sns.countplot(data=data_df, x='day_name', hue='User Type',hue_order=['Annual Member','Casual Member'], palette='hls',order=order)
ridership.set_xlabel('Day Name')
ridership.set_ylabel('Trip Count')
ridership.tick_params(labelsize=12)
ridership.xaxis.label.set_size(14)
ridership.yaxis.label.set_size(14)
plt.title('Bike Share Toronto Ridership 2020-2022',fontsize=14)
plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0.)

#Bike Share Toronto Ridership per hour:
plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ridership = sns.countplot(data=data_df, x='hour', hue='User Type',hue_order=['Annual Member','Casual Member'], palette='hls')
ridership.set_xlabel('Time (hour)')
ridership.set_ylabel('Trip Count')
ridership.tick_params(labelsize=12)
ridership.xaxis.label.set_size(14)
ridership.yaxis.label.set_size(14)
plt.title('Bike Share Toronto Ridership 2020-2022',fontsize=14)
plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0.)

# Bike Share Toronto most popular stations for annual members to start trip(Order in descending):
plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ax=sns.countplot(y=data_df[data_df['User Type']=='Annual Member']['Start Station Name'],data=data_df, palette='coolwarm',order=data_df[data_df['User Type']=='Annual Member']['Start Station Name'].value_counts(ascending=False).index[:5])
ax.set_xlabel('Trip Count')
ax.set_ylabel('Departing Station')
ax.tick_params(labelsize=12)
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)
plt.title('Most Popular 5 Departing Stations (Annual Members)',fontsize=14)

# Bike Share Toronto least popular stations for annual members to start trip(Order in ascending):
plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ax=sns.countplot(y=data_df[data_df['User Type']=='Annual Member']['Start Station Name'],data=data_df, palette='coolwarm',order=data_df[data_df['User Type']=='Annual Member']['Start Station Name'].value_counts(ascending=True).index[:5])
ax.set_xlabel('Trip Count')
ax.set_ylabel('Departing Station')
ax.tick_params(labelsize=12)
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)
plt.title('Least Popular 5 Departing Stations (Annual Members)',fontsize=14)

# Bike Share Toronto most popular stations for annual members to finish trip(Order in descending):
plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ax=sns.countplot(y=data_df[data_df['User Type']=='Annual Member']['End Station Name'],data=data_df, palette='coolwarm',order=data_df[data_df['User Type']=='Annual Member']['End Station Name'].value_counts(ascending=False).index[:5])
ax.set_xlabel('Trip Count')
ax.set_ylabel('Arriving Station')
ax.tick_params(labelsize=12)
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)
plt.title('Most Popular 5 Arriving Stations (Annual Members)',fontsize=14)

# Bike Share Toronto least popular stations for annual members to finish trip(Order in ascending):
plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ax=sns.countplot(y=data_df[data_df['User Type']=='Annual Member']['End Station Name'],data=data_df, palette='coolwarm',order=data_df[data_df['User Type']=='Annual Member']['End Station Name'].value_counts(ascending=True).index[:5])
ax.set_xlabel('Trip Count')
ax.set_ylabel('Arriving Station')
ax.tick_params(labelsize=12)
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)
plt.title('Least Popular 5 Arriving Stations (Annual Members)',fontsize=14)

# Bike Share Toronto most popular stations for Casual Members to start trip(Order in descending):
plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ax=sns.countplot(y=data_df[data_df['User Type']=='Casual Member']['Start Station Name'],data=data_df, palette='viridis',order=data_df[data_df['User Type']=='Casual Member']['Start Station Name'].value_counts(ascending=False).index[:5])
ax.set_xlabel('Trip Count')
ax.set_ylabel('Departing Station')
ax.tick_params(labelsize=12)
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)
plt.title('Most Popular 5 Departing Stations (Casual Members)',fontsize=14)

# Bike Share Toronto Least popular stations for Casual Members to start trip(Order in ascending):
plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ax=sns.countplot(y=data_df[data_df['User Type']=='Casual Member']['Start Station Name'],data=data_df, palette='viridis',order=data_df[data_df['User Type']=='Casual Member']['Start Station Name'].value_counts(ascending=True).index[:5])
ax.set_xlabel('Trip Count')
ax.set_ylabel('Departing Station')
ax.tick_params(labelsize=12)
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)
plt.title('Least Popular 5 Departing Stations (Casual Members)',fontsize=14)

# Bike Share Toronto most popular stations for Casual Members to end trip(Order in descending):
plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ax=sns.countplot(y=data_df[data_df['User Type']=='Casual Member']['End Station Name'],data=data_df, palette='viridis',order=data_df[data_df['User Type']=='Casual Member']['End Station Name'].value_counts(ascending=False).index[:5])
ax.set_xlabel('Trip Count')
ax.set_ylabel('Arriving Station')
ax.tick_params(labelsize=12)
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)
plt.title('Most Popular 5 Arriving Stations (Casual Members)',fontsize=14)

# Bike Share Toronto least popular stations for Casual Members to end trip(Order in ascending):
plt.figure(figsize=(10,5))
sns.set_style('darkgrid')
ax=sns.countplot(y=data_df[data_df['User Type']=='Casual Member']['End Station Name'],data=data_df, palette='viridis',order=data_df[data_df['User Type']=='Casual Member']['End Station Name'].value_counts(ascending=True).index[:5])
ax.set_xlabel('Trip Count')
ax.set_ylabel('Arriving Station')
ax.tick_params(labelsize=12)
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)
plt.title('Least Popular 5 Arriving Stations (Casual Members)',fontsize=14)

"""# Modeling"""

# Split the data frame into X and Y
X = data_df.drop('User Type', axis=1)
y = data_df['User Type']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Work out which columns are numeric and which need to be encoded
cat_cols = X_train.columns[X_train.dtypes == "object"].values
num_cols = X_train.columns[X_train.dtypes != "object"].values

# Drop columns with low predictive value.
drop_cols = ['Trip Id', 'Start Station Name', 'Start Time', 
             'End Station Name', 'End Time', 'Bike Id',
             'Start Station Id', 'End Station Id',
             'hour', 'date_only', 'date',
             'Trip  Duration'
             ]

# Remove columns that will be dropped from the other lists
cat_cols = [i for i in cat_cols if i not in set(drop_cols)]
num_cols = [i for i in num_cols if i not in set(drop_cols)]

print(cat_cols)
print(num_cols)

# Create a data pipeline to encode categoricla data
# and drop unwanted columns.
data_pipeline = ColumnTransformer(
    [
        #("num", "passthrough", num_cols),
        ('scaler', StandardScaler(), num_cols),
        ("cat", OneHotEncoder(), cat_cols),
        ("drop", "drop", drop_cols),
    ]
)

# my_class_weight = {"Annual Member": 20.0,
#                     "Casual Member": 80.0}

# Create a full pipeline using Logistic Regression
# The pipeline will call fit() on the constructed model
full_pipeline = Pipeline([
        ("data", data_pipeline),
        ("model", LogisticRegression(class_weight="balanced"))
    ])

params_grid = {
    "model__random_state" : [42],

}

# Use cross validation to check my model.
# Use Area Under the Curve as it is a good all round measure.
# Create the grid search with the full pipeline. Note this performs cross validation
#cv_pipe = GridSearchCV(full_pipeline, params_grid, cv=2, n_jobs=-1, 
#                     scoring='roc_auc', return_train_score=True, verbose=1)

auc_scores = cross_val_score(full_pipeline, X_train, y_train, 
                          scoring='roc_auc', cv=2, n_jobs=-1)  # roc_auc

# Model validation
print(auc_scores)
print(np.mean(auc_scores))

model = full_pipeline.fit(X_train, y_train)

y_pred_test = model.predict(X_test)
class_names = [str(x) for x in model.named_steps['model'].classes_]
print(classification_report(y_test, y_pred_test, target_names=class_names))

# Make a dataframe so it prints prettier
X_train_prep = data_pipeline.fit_transform(X_train, y_train)

features = data_pipeline.get_feature_names_out()
coef = model.named_steps['model'].coef_[0]
print(len(coef))
for i in np.arange(0,len(coef)):
    print(f"{features[i]} = {coef[i]:.3f}")

order = ["cat__day_name_Monday", "cat__day_name_Tuesday", "cat__day_name_Wednesday", "cat__day_name_Thursday", "cat__day_name_Friday", 
         "cat__day_name_Saturday", "cat__day_name_Sunday"]

sns.set_theme(context='notebook', style='darkgrid', palette='hls', font='sans-serif', font_scale=1, color_codes=True, rc=None)

fig, ax = plt.subplots(figsize=(6,5))

h = sns.barplot(x=coef[20:28], y=features[20:28], order=order)
h.tick_params(labelsize=14)

ax.set(xlabel='Coefficient', ylabel='Weekday')
h.set(xlim=(-2, 2))

plt.show()

order = ["scaler__avg_temperature", "scaler__min_windchill", "scaler__avg_relative_humidity", "scaler__avg_wind_speed", "scaler__rain", "scaler__snow",
         ]

sns.set_theme(context='notebook', style='darkgrid', palette='hls', font='sans-serif', font_scale=1, color_codes=True, rc=None)

fig, ax = plt.subplots(figsize=(6,5))

h = sns.barplot(x=coef[0:6], y=features[0:6], order=order)
h.tick_params(labelsize=14)

ax.set(xlabel='Coefficient', ylabel='Weather')
h.set(xlim=(-2, 2))

#sns.set_context("paper", rc={"font.size":15,"axes.titlesize":15,"axes.labelsize":15, "axes.ticksize":15})   

plt.show()

order = ["cat__hour-bin_0-3", "cat__hour-bin_3-6", "cat__hour-bin_6-9", "cat__hour-bin_9-12", "cat__hour-bin_12-15", "cat__hour-bin_15-18",
         "cat__hour-bin_18-21", "cat__hour-bin_21-23"]

fig, ax = plt.subplots(figsize=(6,5))

h = sns.barplot(x=coef[27:35], y=features[27:35], order=order)
h.tick_params(labelsize=14)

ax.set(xlabel='Coefficient', ylabel='Time of Day')
h.set(xlim=(-2, 2))

#sns.set_context("paper", rc={"font.size":15,"axes.titlesize":15,"axes.labelsize":15, "axes.ticksize":15})   

plt.show()

order = ["cat__month_Jan", "cat__month_Feb", "cat__month_Mar", "cat__month_Apr", "cat__month_May", "cat__month_Jun",
         "cat__month_Jul", "cat__month_Aug", "cat__month_Sep", "cat__month_Oct", "cat__month_Nov", "cat__month_Dec",]

fig, ax = plt.subplots(figsize=(6,10))

h = sns.barplot(x=coef[8:20], y=features[8:20], order=order)
h.tick_params(labelsize=14)

ax.set(xlabel='Coefficient', ylabel='Month')
h.set(xlim=(-2, 2))

#sns.set_context("paper", rc={"font.size":15,"axes.titlesize":15,"axes.labelsize":15, "axes.ticksize":15})   

plt.show()

order = ["cat__duration-min_0-5", "cat__duration-min_5-15", "cat__duration-min_15-25", "cat__duration-min_25-45", "cat__duration-min_45-90", "cat__duration-min_90+",
         ]

fig, ax = plt.subplots(figsize=(6,5))

h = sns.barplot(x=coef[35:41], y=features[35:41], order=order)
h.tick_params(labelsize=14)

ax.set(xlabel='Coefficient', ylabel='Month')
h.set(xlim=(-2, 2))

#sns.set_context("paper", rc={"font.size":15,"axes.titlesize":15,"axes.labelsize":15, "axes.ticksize":15})   

plt.show()

sns.set_style("white")
fig, ax = plt.subplots(figsize=(6,5))

model = full_pipeline.fit(X_train, y_train)
metrics.plot_confusion_matrix(model, X_train, y_train, cmap='Blues_r', values_format=",.0f", ax=ax)