//加密公钥
var PUBLIC_KEY =
  "MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBAJFBnk78A4CN5gBpIV/pGOGqi/CzvwjvXoj2gYXtbEIg+ZxpRrVi7Is6dwIK4+xrDr35ExaN1s4GnyF3g88z93iYpM5URhQTRJ/GGENNlozkLNARRdTJfLuJxBMZHnAGOtuNTXIcIo5/k8klllBYHTqG6xIVnjRN0vsV2UGlnW7VAgMBAAECgYBMoT9xD8aRNUrXgJ7YyFIWCzEUZN8tSYqn2tPt4ZkxMdA9UdS5sFx1/vv1meUwPjJiylnlliJyQlAFCdYBo7qzmib8+3Q8EU3MDP9bNlpxxC1go57/q/TbaymWyOk3pK2VXaX+8vQmllgRZMQRi2JFBHVoep1f1x7lSsf2TpipgQJBANJlO+UDmync9X/1YdrVaDOi4o7g3w9u1eVq9B01+WklAP3bvxIoBRI97HlDPKHx+CZXeODx1xj0xPOK3HUz5FECQQCwvdagPPtWHhHx0boPF/s4ZrTUIH04afuePUuwKTQQRijnl0eb2idBe0z2VAH1utPps/p4SpuT3HI3PJJ8MlVFAkAFypuXdj3zLQ3k89A5wd4Ybcdmv3HkbtyccBFALJgs+MPKOR5NVaSuF95GiD9HBe4awBWnu4B8Q2CYg54F6+PBAkBKNgvukGyARnQGc6eKOumTTxzSjSnHDElIsjgbqdFgm/UE+TJqMHmXNyyjqbaA9YeRc67R35HfzgpvQxHG8GN5AkEAxSKOlfACUCQ/CZJovETMmaUDas463hbrUznp71uRMk8RP7DY/lBnGGMeUeeZLIVK5X2Ngcp9nJQSKWCGtpnfLQ==";
function encryption(objVal) {
  if (typeof objVal != "object" || JSON.stringify(objVal) == '{}') {
    console.log(objVal, '传参错误');
    return false;

  }
  var gx = RandomRange(16)
  // RSA使用公钥加密
  var encrypt = new JSEncrypt();
  encrypt.setPublicKey(PUBLIC_KEY); //设置公钥
  var sk = encrypt.encrypt(gx).toString(); // 对随机数加密

  //按ascii码从小到大排序
  var s_data = sort_ascii(objVal) + gx;
  // md5加密
  var secretSign = CryptoJS.MD5(s_data).toString();
  var newObjVal = JSON.parse(JSON.stringify(objVal)); //拷贝获取参入参数
  newObjVal.secretSign = secretSign;
  return {
    sk: sk,
    data: Encrypt(gx, newObjVal) // AES加密
  }
}
//随机数
function RandomRange(len) {
  var returnStr = "";
  var arr = [
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
  ];
  for (var i = 0; i < len; i++) {
    var index = Math.round(Math.random() * (arr.length - 1));
    returnStr += arr[index];
  }
  return returnStr;
}
//按ascii码从小到大排序
function sort_ascii(obj) {
  var arr = new Array();
  var num = 0;
  Object.keys(obj).forEach(function (key) {
    arr[num] = key;
    num++;
  });
  var sortArr = arr.sort();
  var str = "";
  for (var i = 0; i < sortArr.length; i++) {
    str += obj[sortArr[i]];
  }
  return str;
}
// AES加密
function Encrypt(RandomRange, objVal) {

  var key = CryptoJS.enc.Utf8.parse(RandomRange); //将秘钥转换成Utf8字节数组
  //加密
  var encrypt = CryptoJS.AES.encrypt(
    CryptoJS.enc.Utf8.parse(JSON.stringify(objVal)),
    key,
    {
      iv: CryptoJS.enc.Utf8.parse("0010010000100100"),
      mode: CryptoJS.mode.CBC,
      padding: CryptoJS.pad.Pkcs7,
    }
  );
  return CryptoJS.enc.Base64.stringify(encrypt.ciphertext); //加密后的数据
}
