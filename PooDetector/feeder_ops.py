# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/04_feeder_ops.ipynb (unless otherwise specified).

__all__ = ['CAP_URL', 'PATH_SAVE_FILES', 'PATH_FILE_LOG', 'SLEEP_TIME_BETWEEN_CAPTURE', 'ACTIVATE_PREDICTION',
           'SLEEP_BETWEEN_FEEDING', 'PREDICTION_THRES', 'MAX_FEEDING_SESSIONS_PER_DAY', 'ACTIVATE_FEEDER', 'PATH_MODEL',
           'PATH_FOLDER_SUCCESSFUL_PREDICTIONS', 'FEEDER_URL', 'FEEDER_USER', 'FEEDER_PWD', 'FEEDER_CMD',
           'INFLUX_TOKEN', 'INFLUX_ORG', 'INFLUX_BUCKET', 'INFLUX_URL', 'TlsSMTPHandler', 'get_logger', 'create_folder',
           'get_sunrise', 'get_sunset', 'send_mail_with_pic', 'run_feeder', 'get_influx_api', 'write_to_influx',
           'cap_and_predict']

# Cell
import os
import argparse
from datetime import datetime, timedelta, date
import time
import logging
import numpy as np
import cv2
import sys
import paramiko
import yagmail
from pathlib import Path
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from fastai.vision import *
from fastscript import *
from astral import LocationInfo
from astral.sun import sun
from dateutil import tz

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


# Cell
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


CAP_URL = os.getenv('CAP_URL', default='.')
PATH_SAVE_FILES = os.getenv('PATH_SAVE_FILES', default='data')
PATH_FILE_LOG = os.getenv('PATH_FILE_LOG', default='data/camera_log')
SLEEP_TIME_BETWEEN_CAPTURE = float(os.getenv('SLEEP_TIME_BETWEEN_CAPTURE', default=0.25))


ACTIVATE_PREDICTION = bool(os.getenv('ACTIVATE_PREDICTION', default=False))
SLEEP_BETWEEN_FEEDING = int(os.getenv('SLEEP_BETWEEN_FEEDING', default=3600))
PREDICTION_THRES = float(os.getenv('PREDICTION_THRES', default=0.75))
MAX_FEEDING_SESSIONS_PER_DAY = int(os.getenv('MAX_FEEDING_SESSIONS_PER_DAY', default=4))
ACTIVATE_FEEDER = bool(os.getenv('ACTIVATE_FEEDER', default=False))
PATH_MODEL = os.getenv('PATH_MODEL', default='data')
PATH_FOLDER_SUCCESSFUL_PREDICTIONS = os.getenv('PATH_FOLDER_SUCCESSFUL_PREDICTIONS', default='data/successful')

FEEDER_URL = os.getenv('FEEDER_URL')
FEEDER_USER = os.getenv('FEEDER_USER')
FEEDER_PWD = os.getenv('FEEDER_PWD')
FEEDER_CMD = os.getenv('FEEDER_CMD', default='echo test')


INFLUX_TOKEN=os.getenv('INFLUX_TOKEN')
INFLUX_ORG=os.getenv('INFLUX_ORG')
INFLUX_BUCKET=os.getenv('INFLUX_BUCKET')
INFLUX_URL=os.getenv('INFLUX_URL')


# Cell
class TlsSMTPHandler(logging.handlers.SMTPHandler):
    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        try:

            msg = self.format(record)
            mail = yagmail.SMTP("wilhelm.fritsche@gmail.com")
            mail.send(
                subject="Poodetector Error",
                to=["wilhelm.fritsche@gmail.com"],
                contents=msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


# Cell
def get_logger(log_file=None):
    """
    Initialize global logger and return it.

    :param log_file: log to this file, or to standard output if None
    :return: created logger
    """

    formatter = logging.Formatter(
        fmt='%(asctime)s p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    log = logging.getLogger()
    if len(log.handlers) >= 2:
        return log

    log.setLevel(logging.INFO)
    if log_file is not None:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handler = RotatingFileHandler(
            log_file,
            maxBytes=1024*1024*30,
            backupCount=3)
        handler.setFormatter(formatter)
        log.addHandler(handler)
        handler.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    log.addHandler(handler)

    mail_handler = TlsSMTPHandler(("...", 587), '...', ['...'], '.', ('...', '...'))
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(formatter)
    log.addHandler(mail_handler)


    return log

# Cell
def create_folder(path: Path, foldername):
    """ creates a folder if it does not exist already """
    (path / foldername).mkdir(parents=True, exist_ok=True)
    return path / foldername

# Cell
def get_sunrise():
    """gets the sunrise as an int"""
    city = LocationInfo("Ludesch", "Austria", "Europe/Berlin", 47.2, 9.7)
    s = sun(city.observer, date= datetime.now())
    return int(s["sunrise"].astimezone(tz.tzlocal()).strftime('%H%M'))


def get_sunset():
    """gets the sunset as an int"""
    city = LocationInfo("Ludesch", "Austria", "Europe/Berlin", 47.2, 9.7)
    s = sun(city.observer, date= datetime.now())
    return int(s["sunset"].astimezone(tz.tzlocal()).strftime('%H%M'))

# Cell
def send_mail_with_pic(image:[str,Path]):
    """send a mail with an embedded picture"""
    image = Path(image)
    mail = yagmail.SMTP("wilhelm.fritsche@gmail.com")
    mail.send(
        subject="running feeder",
        to=["wilhelm.fritsche@gmail.com",
            "pernerwuerstel@gmail.com"],
        contents=yagmail.inline(str(image)))

# Cell
def run_feeder():
    """runs feeder"""
    logger = logging.getLogger()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(FEEDER_URL, username=FEEDER_USER, password=FEEDER_PWD)
    ssh_stdin, ssh_stdout, ssh_stder = ssh.exec_command(FEEDER_CMD)
    logger.info(ssh_stdout.read())
    logger.info(ssh_stder.read())


# Cell
def get_influx_api():
    """returns influx write_api"""
    if INFLUX_URL is None:
        return None

    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    return write_api

# Cell
def write_to_influx(path:Path, accuracy, write_api):
    """write datapoint to influx"""
    if INFLUX_BUCKET is not None:
        point = Point("ai")\
            .tag("filename", path.name)\
            .tag("path", str(path))\
            .field("accuracy", float(accuracy))\
            .time(datetime.utcnow(), WritePrecision.NS)
        write_api.write(INFLUX_BUCKET, INFLUX_ORG, point)

# Cell
@call_parse
def cap_and_predict():
    """this function captures camera pictures. To configure this function please use a .env file"""


    logger = get_logger(PATH_FILE_LOG)

    path = Path(PATH_SAVE_FILES)

    current_date = datetime.today().date()
    prev_date = datetime.min.date
    last_cap_time = datetime.min

    last_run_feeder = datetime.min
    num_run_feeder_per_day = 0

    write_api = get_influx_api()

    model = None
    if ACTIVATE_PREDICTION:
        model = load_learner(PATH_MODEL)

    while True:
        time.sleep(10)
        logger.info('outer while loop')

        try:
            cap = cv2.VideoCapture(CAP_URL)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            while cap.isOpened():

                ret, pic = cap.read()

                if ret is False:
                    logger.warning('pic not readable')
                    break

                now = datetime.now()
                current_date = datetime.today().date()
                time_current = int(now.strftime('%H%M'))

                if get_sunrise() > time_current:
                    continue

                if get_sunset() < time_current:
                    continue

                if prev_date != current_date:
                    num_run_feeder_per_day = 0
                    fld_save_to = create_folder(path, current_date.strftime('%Y%m%d'))
                    # reload model
                    if ACTIVATE_PREDICTION:
                        model = load_learner(PATH_MODEL)
                    logger.info(f"msg=update folder to {current_date}")

                now_str = now.strftime('%Y%m%d%H%M%S_%f')
                path_save_file = fld_save_to / (now_str + '.jpg')

                cv2.imwrite(str(path_save_file), pic)

                prev_date = datetime.today().date() #assign new date to compare to

                prediction = None
                if ACTIVATE_PREDICTION:
                    img = open_image(path_save_file)
                    prediction = model.predict(img)[2][0].numpy()
                    folder =  Path(PATH_FOLDER_SUCCESSFUL_PREDICTIONS) / current_date.strftime('%Y%m%d')

                    #influx
                    write_to_influx(path_save_file, prediction, write_api)


                    if prediction >= PREDICTION_THRES:
                        logger.info('successful prediction')
                        folder = create_folder(Path(PATH_FOLDER_SUCCESSFUL_PREDICTIONS),
                                               current_date.strftime('%Y%m%d'))
                        img.save(folder / path_save_file.name) #save also  in a special folder
                    elif last_cap_time >= datetime.now() or float(prediction) < 0.1:
                        path_save_file.unlink()
                    else:
                        last_cap_time = datetime.now() + timedelta(seconds=SLEEP_TIME_BETWEEN_CAPTURE)



                if ACTIVATE_FEEDER and ACTIVATE_PREDICTION:
                    if PREDICTION_THRES <= prediction:
                        if (last_run_feeder + timedelta(seconds=SLEEP_BETWEEN_FEEDING) < datetime.now()
                            and num_run_feeder_per_day <= MAX_FEEDING_SESSIONS_PER_DAY):

                            last_run_feeder = datetime.now()
                            num_run_feeder_per_day += 1
                            logger.info(f"running feeder last_run_feeder=" +
                                        f"{last_run_feeder} " +
                                        f"num_run_feeder_per_day={num_run_feeder_per_day} " +
                                        f"SLEEP_BETWEEN_FEEDING={SLEEP_BETWEEN_FEEDING} " +
                                        f"MAX_FEEDING_SESSIONS_PER_DAY={MAX_FEEDING_SESSIONS_PER_DAY}")
                            path_image = folder / path_save_file.name
                            send_mail_with_pic(path_image)
                            run_feeder()
                #time.sleep(SLEEP_TIME_BETWEEN_CAPTURE)

        except Exception as e:
            logger.error(e)

        finally:
            cap.release()
            cv2.destroyAllWindows()