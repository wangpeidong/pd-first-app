from flask import jsonify, flash, redirect, url_for, session
from flask_mail import Mail
from functools import wraps
import pandas_datareader.data as web

import datetime, os

import numpy as np
from sklearn import preprocessing, svm
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

# Define decorator/wrapper
def privilege_login_required(privilege):
    def login_required(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if privilege:
                if "username" in session and privilege == session["username"]:
                    return f(*args, **kwargs)
                else:
                    flash("You must login with privilege first !")
                    return redirect(url_for("homepage"))
            else:
                if "logged_in" in session:
                    return f(*args, **kwargs)
                else:
                    flash("You must login first !")
                    return redirect(url_for("homepage"))
        return wrap
    return login_required

def set_mailer(app, server, username, password):
    app.config.update(
        DEBUG=True,
        #EMAIL SETTINGS
        MAIL_SERVER = server,
        MAIL_PORT = 465,
        MAIL_USE_SSL = True,
        MAIL_USERNAME = username,
        MAIL_PASSWORD = password
    )
    mailer = Mail(app)
    return mailer

def get_files_list(dir):
    files = []
    # r=root, d=directories, f=files
    for r, d, f in os.walk(dir):
        for file in f:
            # strip app.root_path 
            files.append(os.path.join(r, file).split(dir, 1)[1])
    return files

def source_stock_price(symbol, start = datetime.datetime(2015, 1, 1)):
    end = datetime.datetime.now()
    df = web.DataReader(symbol, "yahoo", start, end)
    df.reset_index(inplace = True)
    df.set_index("Date", inplace = True)

    return df

def data_regression(df):
    df['HL_PCT'] = (df['High'] - df['Low']) / df['Adj Close'] * 100.0
    df['PCT_change'] = (df['Adj Close'] - df['Open']) / df['Open'] * 100.0
    df = df[['Adj Close', 'HL_PCT', 'PCT_change', 'Volume']]

    forecast_col = 'Adj Close'
    df.fillna(value = -99999, inplace = True)
    forecast_out = 10 # 10 days
    df['label'] = df[forecast_col].shift(-forecast_out)

    X = np.array(df.drop(['label'], 1))
    X = preprocessing.scale(X)
    X_lately = X[-forecast_out:]
    X_2nd_lately = X[-2*forecast_out:-forecast_out] 
    X = X[:-forecast_out*2] # Feature
    y = np.array(df['label'][:-forecast_out*2]) # Label

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2)
    #clf = svm.SVR()
    clf = LinearRegression() # Classifier
    clf.fit(X_train, y_train)
    confidence = clf.score(X_test, y_test)

    last_col = len(df.columns)
    df['Forecast'] = np.nan

    # Comparing set with Adj Close using 2nd X_lately period feature
    comparing_set = clf.predict(X_2nd_lately) 
    for idx, val in enumerate(comparing_set):
        df.iloc[-forecast_out + idx, last_col] = val

    # Future set based on X_lately period feature
    forecast_set = clf.predict(X_lately)
    last_date = df.iloc[-1].name
    last_unix = last_date.timestamp()
    one_day = 86400 # seconds in a day
    next_unix = last_unix + one_day
    for val in forecast_set:
        next_date = datetime.datetime.fromtimestamp(next_unix)
        # exclude weekend
        while next_date.weekday() > 4:
            next_unix += 86400
            next_date = datetime.datetime.fromtimestamp(next_unix)

        next_unix += 86400
        df.loc[next_date, 'Forecast'] = val

    return confidence, df

def add_range_button(fig):
    # centered title, left aligned by default
    fig.update_layout(xaxis = dict(
                    rangeselector = dict(
                        buttons = list([
                            dict(count = 5,
                                 label = '1w',
                                 step = 'day',
                                 stepmode = 'backward'),
                            dict(count = 10,
                                 label = '2w',
                                 step = 'day',
                                 stepmode = 'backward'),
                            dict(count = 1,
                                 label = '1m',
                                 step = 'month',
                                 stepmode = 'backward'),
                            dict(count = 3,
                                 label = '3m',
                                 step = 'month',
                                 stepmode = 'backward'),
                            dict(count = 6,
                                 label = '6m',
                                 step = 'month',
                                 stepmode = 'backward'),
                            dict(count = 1,
                                 label = 'YTD',
                                 step = 'year',
                                 stepmode = 'todate'),
                            dict(count = 1,
                                 label = '1y',
                                 step = 'year',
                                 stepmode = 'backward'),
                            dict(step = 'all')
                        ])
                    ),
                    rangeslider_visible = False
    ))
    # rangebreak does not work with update_layout somehow
    fig.update_xaxes(
        rangebreaks = [
                dict(bounds = ['sat', 'mon'])
            ]
    )
    return fig
