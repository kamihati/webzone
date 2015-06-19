// JavaScript Document
//设置页面文本框控件的默认内容。随焦点的得到和失去而改变
//参数描述
//eid: 文本控件id
//txt: 文本控件默认要显示的文字
function set_input_default(eid, txt){
	var elm = $("#" + eid);
    elm.focus(function(){
		if($.trim(elm.val()) == txt)
			elm.val("");
	});

    elm.blur(function(){
	    if($.trim(elm.val()) == "")
			elm.val(txt);
    });
}

//获取当前客户端时间戳
function get_timestamp(){
	return Date.parse(new Date());
}


//根据指定参数生成后台管理页面列表分页部分html代码
function get_yema_html(data_count, page_index, page_size){
    var html = '<span>共<b>' + data_count + '</b>条记录</span>';
    html += '<span>每页<b>' + page_size + '</b>个</span>';
    if(page_index > 1){
        html += '<a href="javascript:search(1)">首页</a>';
        html += '<a href="javascript:search(' + (page_index - 1) + ')" class="s1">上一页</a>';
    }
    var page_count = parseInt(data_count / page_size);
    if(data_count % page_size > 0)
        page_count += 1;

    if(page_count > page_index){
        html += '<a href="javascript:search(' + (page_index + 1) + ')" class="s1">下一页</a>';
        html += '<a href="javascript:search(' + page_count + ')">末页</a>'
    }
    html += '<span>第<b>' + page_index + '</b>页</span>';
    html += '<span>总共<b>' + page_count + '</b>页</span>';
    return html;
}

//上传文件
//obj为input file对象

//ele_name: 存储上传文件的返回值所存储的hidden控件
//link_id: 上传后的文件访问地址所使用的 <a>元素id
//loading_id: loading图片的控件id

function check_upload_file(obj,  ele_name, link_id, loading_id){
	if(link_id == null)
	    link_id = "a_ajax_img";

    var filename = obj.value;
	if(loading_id == null)
		loading_id = "loading";

    //检查文件类型
    var exName = filename.substr(filename.lastIndexOf(".")+1).toUpperCase();

	//ajax 上传图片
	$("#" + loading_id).show();
	$.ajaxFileUpload({
		url:"/manager/ajax_upload_file/",
		secureuri:false,
		fileElementId:obj.id,
		dataType: 'text',
		success: function (data, status){
			var json_data = JSON.parse(data);
			if (json_data.code == 1){
				$("#" + link_id).attr("href", "/media/" + json_data.data.path);
				$("#" + link_id).show();
				$("#" + ele_name).val(json_data.data.path);
			} else {
				alert(json_data.data);
			}

			$("#" + loading_id).hide();
		},
		error: function (data, status, e)
		{
			alert(e);
			$("#" + loading_id).hide();
		}
	});

}



//上传图片
//obj为input file对象
//enable_ext: 允许上传的文件类型扩展名列表  例如 ['JPEG','GIF', 'JPG']
//ele_name: 存储上传文件的返回值所存储的hidden控件
//link_id: 上传后的文件访问地址所使用的 <a>元素id
//loading_id: loading图片的控件id

function check_img(obj, enable_ext, ele_name, link_id, loading_id){
	if(link_id == null)
	    link_id = "a_ajax_img";

    var filename = obj.value;
	if(loading_id == null)
		loading_id = "loading";

    //检查文件类型
    var exName = filename.substr(filename.lastIndexOf(".")+1).toUpperCase();

    if(enable_ext.indexOf(exName) > -1){
        //ajax 上传图片
        $("#" + loading_id).show();
		$.ajaxFileUpload({
			url:"/manager/ajax_upload_img/",
			secureuri:false,
			fileElementId:obj.id,
			dataType: 'text',
			success: function (data, status){
				var json_data = JSON.parse(data);
				if (json_data.code == 1){
					$("#" + link_id).attr("href", "/media/" + json_data.data.path);
					$("#" + link_id).show();
					$("#" + ele_name).val(json_data.data.path);
				} else {
					alert(json_data.data);
				}

				$("#" + loading_id).hide();
			},
			error: function (data, status, e)
			{
				alert(e);
				$("#" + loading_id).hide();
			}
		});
    } else {
        alert("只能上传这些类型的文件：" + enable_ext);
    }
}
 

//根据传入的setting 配置与 nodes节点数据初始化容器内容。一般为ul元素
function ztree_init(eleName, setting, nodes){
	$.fn.zTree.init($("#" + eleName), setting, nodes);
}


//获取checkbox 选中的值
function get_checkbox_val(ele_name){
	var result = "";
	$("input[name=" + ele_name + "]:checked").each(function(index, element) {
		result += "," + $(element).val();
	});
	if(result != ""){
		result = result.substr(1)
	}
	return result;
}



//选中或反选指定name的控件
function check_item(ele_name){
	var check = false;
	$('input[name=' + ele_name + ']').each(function(index, element) {
		if(index == 0){
			if($(element).attr("checked")){
				check = "checked";
			}
		}else{
			$(element).attr("checked", check);
		}
	});
}