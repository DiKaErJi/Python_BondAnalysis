/**
 * Created by pkk on 2017/4/23.
 */
jQuery.support.cors = true;
$(function(){
    $("#username").val($.cookie("username"));
    $("#password").val($.cookie("password"));
});
function login(){
    var username = $("#username").val();
    var password = $("#password").val();
    var params = {};
    params.userName = username;
    params.userPwd = hex_sha1(password);
    console.log(params);
    $.ajax({
        cache: false,
        type: "post",
        url:'http://10.40.107.154:8088/easysightInt/rest/sys/login',
        contentType: "application/json;charset=utf-8",
        async: false,
        data:JSON.stringify(params),
        error: function(request) {
            alert("登录失败！");
        },
        success: function(data, textStatus, request) {
            console.log(data);
            switch(data.statusCode){
                case 1:
                    $.cookie("username",username,7);
                    if($("#isCheck").prop("checked")){$.cookie("password",password,7);}else{$.cookie("password",'');}
                    //$.cookie("loginTime",getCurrentTime(),7);
                    window.location.href= "index.html";
                    break;
                case 0:
                    alert("登录账号不存在！");
                    break;
                case -1:
                    alert("密码有误！");
                    break;
                default:
                    alert("登录失败！"); break;
            }
        }
    });
}


