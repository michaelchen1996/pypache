import re

rules=[]

def rewrite(srcUrl):
    print("rewrite url: " + srcUrl)
    try:
        for pair in rules:
            retUrl = pair[1]
            m = pair[0].match(srcUrl)
            # if it matches the rule
            mlen = len(m.groups()) 
            if mlen>0:
                for i in range(1,mlen+1):
                    subi = '$' + str(i)
                    retUrl = retUrl.replace(subi,m.group(i))
                    break
            return retUrl
    except Exception as e:
        print('url rewrite error: ' + repr(e))
        return srcUrl
        
def __init():
    with open('./etc/rules.conf','r') as f:
        for line in f.readlines():
            line = line.strip()
            if not line.startswith('#') and len(line) > 0:
                results = line.split(' ')
                pair=[]
                pair.append(re.compile(' '.join(results[:-1])))
                pair.append(results[-1])
                print(pair)
                rules.append(pair)

__init()
