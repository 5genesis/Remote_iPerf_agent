import os
import yaml
from flask import Flask, jsonify, request
from iperfExecutor import iPerf
from iperfExecutor.iperfConfig import iPerfConfig

app = Flask(__name__)

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(THIS_FOLDER, 'config.yml'), 'r', encoding='utf-8') as file:
    data = yaml.safe_load(file)

iPerf.Initialize(data['IPERF_PATH'])


def errorResponse(message, error):
    print(f'{message}: {error}')
    return jsonify({'Status': 'Error', 'Message': message, 'Error': f'{error}'}), 403


@app.route('/Iperf', methods=['POST'])
@app.route('/Iperf/<pathParameters>', methods=['GET'])
def Iperf(pathParameters: str = ""):
    mode = 'server'
    try:
        if request.method == 'POST':
            jsonBody = str(request.json)
            parameters = jsonBody[1:-1].replace('\'', '').split(',')
        else:
            if iPerfConfig.formatValidation(pathParameters):
                parameters = pathParameters[1:-1].split(',')
            else:
                return errorResponse('Error executing iPerf', 'Wrong parameter format')

        for param in parameters:
            if '-c' in param:
                mode = "client"
                break
        iPerf.Iperf(parameters)
        return jsonify({'Status': 'Success', 'Message': f'Successfully executed iPerf {mode}'})

    except Exception as error:
        return errorResponse(f'Error executing iPerf {mode}', error)


@app.route('/Close', methods=['GET'])
def Close():
    try:
        iPerf.Close()
        return jsonify({'Status': 'Success', 'Message': 'Successfully closed iPerf'})
    except Exception as error:
        return errorResponse('Error closing iPerf', error)


@app.route('/LastRawResult', methods=['GET'])
def LastRawResult():
    try:
        return jsonify({'Status': 'Success', 'Message': 'Successfully retrieved last raw result',
                        'Result': iPerf.LastRawResult()})
    except Exception as error:
        return errorResponse('Error retrieving last raw result', error)


@app.route('/LastJsonResult', methods=['GET'])
def LastJsonResult():
    try:
        return jsonify({'Status': 'Success', 'Message': 'Successfully retrieved last json result',
                        'Result': iPerf.LastJsonResult()})
    except Exception as error:
        return errorResponse('Error retrieving last json result', error)


@app.route('/LastError', methods=['GET'])
def LastError():
    try:
        return jsonify({'Status': 'Success', 'Message': 'Successfully retrieved last error',
                        'Error': iPerf.LastError()})
    except Exception as error:
        return errorResponse('Error retrieving last error', error)


@app.route('/StartDateTime', methods=['GET'])
def StartDateTime():
    return jsonify({'Status': 'Success', 'Message': f'Start date time {iPerf.StartDateTime()}'})


@app.route('/IsRunning', methods=['GET'])
def IsRunning():
    return jsonify({'Status': 'Success', 'Message': f'iPerf is running: {iPerf.IsRunning()}'})


if __name__ == '__main__':
    app.run()
