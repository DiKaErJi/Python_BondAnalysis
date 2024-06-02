import hashlib  # 导入hashlib库，该库提供了常见的加密算法，如MD5、SHA-1等

def hash_code(s, salt='nemo'):
    # 定义一个函数 hash_code，接受两个参数：
    # s：要加密的字符串
    # salt：加密使用的盐值，默认为 'nemo'

    md5 = hashlib.md5()
    # 创建一个MD5加密对象，md5() 是 hashlib 模块提供的用于生成MD5散列对象的方法

    s += salt
    # 将盐值加到输入字符串的末尾，以增加安全性，防止彩虹表攻击
    # 例如，如果输入字符串是 '123'，盐值是 'nemo'，则 s 变成 '123nemo'

    md5.update(s.encode('utf-8'))
    # 对合并后的字符串进行MD5加密
    # 首先，将字符串编码为UTF-8字节序列，因为hashlib的update()方法接受字节序列作为输入

    return md5.hexdigest()
    # 返回加密后的十六进制表示形式，hexdigest() 方法生成一个包含32个字符的十六进制数字符串

if __name__ == '__main__':
    # 该部分用于当脚本作为主程序运行时执行下面的代码块
    # 这有助于将模块作为脚本独立运行时进行测试

    print(hash_code('123'))
    # 调用 hash_code 函数，传入字符串 '123'
    # 打印加密后的结果
