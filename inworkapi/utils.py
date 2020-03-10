import json

class JSendResponse:
    SUCCESS = 'success'
    FAIL = 'fail'
    ERROR = 'error'
    statuses = [SUCCESS, FAIL, ERROR]


    def __init__(self, status, data=None, message=None):
        
        if not status in self.statuses:
            raise ValueError('Status must be one of these values: {}'.format(self.statuses))
        
        self._status = status

        if not status == self.ERROR and message:
            raise ValueError('Only a response with a status \'error\' can have \'message\' attribute ')

        self._data = data
        self._message = message


    @property
    def status(self):
        return self._status


    @property
    def data(self):
        return self._data


    @property
    def message(self):
        return self._message


    @data.setter
    def data(self, value):
        self._data = value


    @message.setter
    def message(self, value):
        if self.status == self.ERROR:
            self._message = value
        else:
            raise ValueError('Can only set a mesage on a response with an \'error\' status'
                    .format(self._status))


    def make_json(self):
        response_dict = {}
        response_dict['status'] = self._status
        
        if self.data:
            response_dict['data'] = self.data
        elif self.status == self.FAIL or self.status == self.SUCCESS:
            response_dict['data'] = None
        
        if self.message:
            response_dict['message'] = self._message
        elif self.status == self.ERROR:
            response_dict['message'] = None

        #return json.dumps(response_dict, indent=4)
        return response_dict