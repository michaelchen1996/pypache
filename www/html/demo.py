from WebServerAPI import *


class MyServlet(HttpServlet):
    def _doGET(self, echo):
        print("test str in console")
        cmd = self.getParameter("cmd")
        if cmd is None or cmd == '':
            echo("参数cmd是必须的,请输入")
        if cmd == '0':
            echo("动态测试页面")
        elif cmd == '1':
            echo("动态测试页面2")
        elif cmd == 'calc':
            exp = self.getParameter("exp")
            if cmd is None or cmd == '':
                echo("参数exp是必须的,请输入")
            echo("<html><body><h1>" + exp + '=' + str(eval(exp)) + "</h1></body></html>")
        else:
            echo("不支持的输入")

    def _doPOST(self, echo):
        super()._doPOST(echo)


MyServlet()
