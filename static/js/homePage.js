/**
 * Created by pkk on 2017/5/9.
 */
var iframHeiht = document.body.scrollHeight-70;

$(function(){
    $(".tableNorth").height(iframHeiht/3);
    $(".panelCenter").height(iframHeiht/3);
    $(".panelSouth").height(iframHeiht/3);

});