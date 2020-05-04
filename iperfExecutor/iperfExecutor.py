import os
import signal
import subprocess
from typing import List, Dict
from datetime import datetime, timezone
from threading import Thread
from iperfExecutor.iperfConfig import iPerfConfig


class iPerf:
    isRunning = False
    executable: str = None
    rawResult: List[str] = []
    jsonResult: List[Dict] = []
    error: List[str] = []
    startTime: datetime = None
    isServer = False
    processPID: int = -1

    @classmethod
    def Initialize(cls, executable: str):
        cls.executable = executable

    @classmethod
    def Iperf(cls, parameters: List[str]):
        params = iPerfConfig.parseParameters(parameters)
        return cls.execute(params)

    @classmethod
    def Close(cls):
        if not cls.isRunning or cls.processPID == -1:
            raise RuntimeError('iPerf is not running')

        os.kill(cls.processPID, signal.SIGTERM)
        cls.processPID = -1
        cls.isRunning = False
        return 1


    @classmethod
    def LastRawResult(cls):
        if cls.isRunning:
            raise RuntimeError("iPerf is still running")

        print(f'Last Raw Result: {cls.rawResult}')
        return cls.rawResult

    @classmethod
    def LastJsonResult(cls):
        if cls.isRunning:
            raise RuntimeError("iPerf is still running")

        print(f'Last Json Result: {cls.jsonResult}')
        return cls.jsonResult

    @classmethod
    def LastError(cls):
        if cls.isRunning:
            raise RuntimeError("iPerf is still running")

        print(f'Last Error: {cls.error}')
        return cls.error


    @classmethod
    def StartDateTime(cls):
        print(f'Start Date Time: {cls.startTime}')
        return cls.startTime

    @classmethod
    def IsRunning(cls):
        print(f'Is Running: {cls.isRunning}')
        return cls.isRunning

    @classmethod
    def execute(cls, parametersDict: Dict) -> None:
        if cls.executable is None:
            raise RuntimeError('Running iPerf without executable')
        if cls.isRunning:
            raise RuntimeError('iPerf already running')

        # Shorten long parameters format
        parametersDict = iPerfConfig.shortenParameters(parametersDict)

        # Force format to Mbits/sec and interval to 1s if not present
        parametersDict['-f'] = 'm'
        if '-i' not in parametersDict.keys():
            parametersDict['-i'] = '1'
        interval = int(parametersDict['-i'])

        if '-u' in parametersDict.keys() or '-U' in parametersDict.keys():
            protocol = 'UDP'
        else:
            protocol = 'TCP'

        # 'P' parameter must be after client host and port
        if '-P' in parametersDict.keys():
            parallelEnabled = True
            moveToLast = parametersDict.pop('-P')
            parametersDict['-P'] = moveToLast
        else:
            parallelEnabled = False

        parameters = []
        for key, value in parametersDict.items():
            parameters.append(key)
            if len(value) != 0:
                parameters.append(value)

        params = [cls.executable, *parameters]
        print(params)
        Thread(target=cls.async_task, args=(params, protocol, parallelEnabled, interval)).start()
        return None

    @classmethod
    def stdout(cls, process: subprocess.Popen, protocol: str, parallelEnabled: bool, interval: int):
        pipe = process.stdout

        for line in iter(pipe.readline, b''):
            try:
                line = line.decode('utf-8').rstrip()
            except Exception as e:
                line = f'DECODING EXCEPTION: {e}'

            if 'error' in line or 'failed' in line:
                cls.error.append(line)

            parse = iPerfConfig.parseIperfResult(line, protocol, parallelEnabled, cls.startTime, interval)
            if parse:
                cls.rawResult.append(line)
                cls.jsonResult.append(parse)

    @classmethod
    def async_task(cls, params: List[str], protocol: str, parallelEnabled: bool, interval: int):
        cls.isRunning = True
        cls.rawResult = []
        cls.jsonResult = []
        cls.error = []
        cls.startTime = datetime.now(timezone.utc)
        try:
            process = subprocess.Popen(params, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            cls.processPID = process.pid

            if '-c' in params:
                cls.isServer = False
                print('Client running')
            else:
                cls.isServer = True
                print('Server running')

            cls.stdout(process, protocol, parallelEnabled, interval)
            process.wait()
        except Exception as e:
            print(f'Error in process: {e}')
        finally:
            cls.isRunning = False

        if not cls.isServer:
            print('Client finished')
        else:
            print('Server finished')
