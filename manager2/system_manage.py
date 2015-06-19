#coding:utf-8

import datetime
import json
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect

from utils.decorator import print_trace
from utils.decorator import manager_required
from utils.db_handler import get_cursor


from library.models import Library
from account.models import AuthUser
from message.models import Message
from widget.models import WidgetGas
from account.models import AuthActionLog,AuthMessage
from manager.models import ManagerActionLog

from library.handler import get_region


@print_trace
@manager_required
def list_xtxx(request):
    '''
    系统消息
    editor: kamihati 2015/5/25
    :param request:
    :return:
    '''
    sheng = request.GET.get('province', '')
    shi = request.GET.get('city', '')
    xian = request.GET.get('country', '')
    library_id = request.GET.get('library', 0)
    library_id = int(library_id) if library_id != '' else 0
    page_index = int(request.GET.get("page_index", 1))
    page_size = request.GET.get("page_size", 15)
    search_text = request.GET.get('search_text', '')
    result = dict()
    return render(request, 'manager2/system/list_xtxx.html', result)


@print_trace
@manager_required
def log_delete(request):
	"""
	删除留言消息
	"""
	id = request.REQUEST.get("id","")
	if not id :
		HttpResponse("请重新操作")
	else:
		try:
			am = AuthMessage.objects.get(id=id)
			am.status = -2 
			am.save() 
			HttpResponseRedirect("/manager2/list_xtxx/") #刷新页面

		except:
			HttpResponse(u"操作失败亲，请确认你的权限")

@print_trace
@manager_required		
def list_lygl(request):
	page_size = request.REQUEST.get('page_size',20)
	page_index = request.REQUEST.get('page_index',1)
	data = Message.objects.objects.filter(reply=False).order_by("-create_time")
	data_count = data.count()
	data_dict = {"data_count":data_count,"page_index":page_index,"data":data[(page_index-1)*page_size:page_index*page_size]}
  

    
	return render_to_response(
				"manager2/system/list_lygl.html",
				data_dict,
	              )
@print_trace
@manager_required	
def lygl_delete(request):
	m_id = request.REQUEST.get('id',None)
	ms = Message.objects.get(id=m_id)
	ms.status = 1
	ms.save()
	return HttpResponseRedirect('/manager2/list_lygl/') # 刷新页面

def lygl_reply(request):
	m_id = request.REQUEST.get("id",None)
	# title= request.REQUEST.get("title",None)
	content = request.REQUEST.get("content",None)
	name = request.REQUEST.get('name',None)
	email = request.REQUEST.get('email',None)
	suggestion = request.REQUEST.get("suggestion",None)
	if content and name and email:
		return HttpResponse(u"各项不能为空")
	if not m_id:
		return HttpResponse(u'请重新回复')
	try:
		Message.objects.create(
			reply_id = m_id,
			suggestion = suggestion,
			name=name,
			email=email,
			user_id = request.user.id)
		return HttpResponse(u"回复成功")
	except:
		return HttpResponse(u"回复失败，请查看权限问题")

@print_trace
@manager_required	
def list_jygl(request):
	key = request.REQUEST.get("search_text","")
	page_index = request.REQUEST.get("page_size",1)
	page_size = request.REQUEST.get("page_size",20)
	if key:
		results = WidgetGas.objects.filter(content=key).order_by("-create_time") 
	else:
		results = WidgetGas.objects.filter().order_by("-create_time")
	data_count = results.count() 
	result = results[(page_index-1)*page_size:page_index*page_size]
	if key :
		data = {"data_count":data_count,"page_size":page_size,\
		"result":result,"search_text":key}
	else:
		data = {"data_count":data_count,"page_size":page_size,\
		"result":result}
	
	return render_to_response(
				"manager2/system/list_jygl.html",
				data,
	              )
@print_trace
@manager_required
def edit_and_update(request):
	"""
	feedback 在刷新网页的时候才显示
	"""
	g_id = request.REQUEST.get("id",0)
	content = request.REQUEST.get("content","")
	if g_id:
		wo = WidgetGas.objects.get(id=g_id)
		wo.content = content
		wo.update_time = datetime.datetime.now()
		wo.save() 
		feedback = u"修改成功"
	else:
		wo = WidgetGas()
		wo.content = content
		wo.user = request.user
		wo.library =Library.objects.get(user=request.user)
		wo.create_time = datetime.datetime.now()
		wo.update_time = datetime.datetime.now()
		wo.save() 
        feedback = u"创建成功"
        return HttpResponseRedirect("/manager2/list_jygl/?feedback=%s" % feedback)

def wiget_delete(request):
	g_id = request.REQUEST.get("id",0)
	if g_id:
		return HttpResponse("请刷新页面后重新操作")
	else:
		WidgetGas.objects.get(id=g_id)
		feedback = u"创建成功"
		return HttpResponseRedirect("/manager2/list_jygl/?feedback=%s" %feedback)  


def list_grrz(request):
    sheng = request.REQUEST.get("province",None)
    shi = request.REQUEST.get("city",None)
    xian = request.REQUEST.get("country",None)
    xiang = request.REQUEST.get("street",None)
    key = request.REQUEST.get("search_text","")
    page_size = request.REQUEST.get("page_size",20)
    page_index = request.REQUEST.get("page_index",1)
    data_dict = dict() 
    if sheng :
        data_dict["province"] = sheng
    if shi:
        data_dict["city"] = shi
    if xian:
        data_dict["region"] = xian
    if data_dict:
        librays = Library.objects.filter(**data_dict)
    if key:
        results = AuthActionLog.objects.filter(library__in = librays,content__contains=key,user__name__contains=key)
    else:
        results = AuthActionLog.objects.all()

    data_count = results.count()
    data = {"data_count":data_count,"sheng":sheng, "shi":shi,"xian":xian,\
    "search_text":key,"results":results,"page_size":page_size,\
    "page_index":page_index} 
    return render_to_response('/manager2/system/list_grrz.html',data,)

def grrz_delete(request):
    """
    个人操作日志的删除
    """
    #todo 权限问题
    g_id = request.REQUEST.get("id")
    if not g_id:
        HttpResponse("对不起你的操作有问题")
    try:
        AuthActionLog.objects.get(id=g_id).delete()
        HttpResponseRedirect("manager2/list_grrz/?feedback=%s" % u"成功删除了")
    except:
        HttpResponse("联系管理员吧，删除不了") 


def list_manager_log(request):
    sheng = request.REQUEST.get("province","")
    shi = request.REQUEST.get("city","")
    xian = request.REQUEST.get("country","")
    library_id = request.REQUEST.get("library_id","")
    key = request.REQUEST.get("search_text","")
    page_size = request.REQUEST.get("page_size",20)
    page_index = request.REQUEST.get("page_index",1)
    data_dict = dict()
    if sheng:
        data_dict['i']
    if data_dict:
        librarys = Library.objects.filter(**data_dict)
	if key: 
         if key:
            results = ManagerActionLog.objects.filter(library__in = \
            librarys,content__contains=key,user__name__contains=key,status=0)
    else:
        results = ManagerActionLog.objects.filter(status=0)

    provinces = get_region(0)
    citys = get_region(provinces[0])
    regions = get_region(citys[0])
    librarys = Library.objects.all().values_list('id', 'lib_name')

    data_count = results.count()
    page_count = data_count/int(page_size)+1
    data = {"data_count":data_count,"sheng":sheng,"shi":shi,"xian":xian,\
    "key":key,"results":results[(int(page_index)-1)*int(page_size):int(page_index)*int(page_size)],"page_size":int(page_size),\
    "page_index":page_index,"page_pre":int(page_index)-1,"page_next":int(page_index)+1,"page_count":page_count,"provinces":provinces,\
    "citys":citys,"regions":regions,"librarys":librarys}

    return render_to_response(
        "manager2/system/list_czrz.html",
        data,
       )

def m_log_delete(request):
    """
    个人操作日志的删除
    """
    #todo 权限问题
    g_id = request.REQUEST.get("id")
    kargs = request.REQUEST
    kargs['id']
    params = ""
    for key in kargs:
        if key:
            params+="&"+str(key)+"="+str(kargs[key])

    try:
        ma = ManagerActionLog.objects.get(id=g_id)
        ma.status =1
        ma = ma.save()
        return HttpResponseRedirect("/manager2/list_czrz/?feedback=%s" % u"成功删除了"+params)
    except:
        return HttpResponseRedirect("/manager2/list_czrz/?feedback=%s" % u"没有删除了"+params)
