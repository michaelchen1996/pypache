import argparse


class HttpServlet(object):
    def __init__(self):
        parser = argparse.ArgumentParser()
        # 从命令行获取数据路径,默认 MINIST_data
        parser.add_argument('--pipe_name', type=str,
                            help='parameter pipe_name is required')
        parser.add_argument('--data', type=str,
                            help='parameter data is required')
        self.data = eval(parser.parse_args().data)
        self.pipe = open(parser.parse_args().pipe_name, 'w')
        self.parameters = self.data['params']
        self.cookie = self.data['cookie']
        self.reqType = self.data['reqType']

    def getCookie(self):
        return self.cookie

    def getParameter(self, param):
        if param in self.parameters:
            return self.parameters[param]
        return None

    def getRequestType(self):
        return self.reqType

    def setContentType(self, type):
        pass

    # 调用此函数将立即返回
    def setResponseCode(self, code):
        pass

    def printToWeb(self, text):
        self.pipe.write("out:" + text + "\n")
        pass

    def setCookie(self, set_cookie):
        pass


httpServlet = HttpServlet()
