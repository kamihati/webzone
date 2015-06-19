# coding: utf-8
'''
Created on 2015/3/20

@author: kamihati
'''
from django.conf.urls import patterns, include, url
from django.views.decorators.cache import never_cache
from django.http import HttpResponse


@never_cache
def action(request, url):
    print url
    if not request.user or not request.user.is_staff or not url:
        return HttpResponse(u'没有权限访问请求的资源')
    from manager import misaction
    actionfunc = getattr(misaction, url)
    return actionfunc(request)

# 增加后台公共管理的url
urlpatterns = patterns(
    'manager2',
    (r'^$', 'views.index'),
    (r'^login/$', 'views.login'),
    (r'^logout/$', 'views.logout'),
    (r'^api_valify_img/$', 'views.api_valify_image')
)

# 增加后台用户管理的url
urlpatterns += patterns(
    'manager2.admin_manage',
    # 二级管理员管理
    (r'^admin/$', 'level_2_manager'),
    # 机构管理员管理
    (r'^admin/library/$', 'library_manager'),
    # 机构信息修改
    (r'^admin/library_edit/$', 'library_edit'),
    # 机构信息修改明细页
    (r'^admin/library_edit2/$', 'library_edit2'),
    # 机构普通管理员管理
    (r'^admin/library_admin/$', 'library_admin'),
    # 会员管理
    (r'^admin/user/$', 'user_manager'),
    # 过期机构管理
    (r'^admin/old_library/$', 'old_library_manager'),
)


# 增加后台个人创作管理
urlpatterns += patterns(
    'manager2.person_creator_manage',
    # 个人创作管理首页。个人作品列表
    (r'^person_creator/$', 'person_creator_default'),
    # 个人创作管理首页。个人作品列表(待审核)
    (r'^person_creator_wait/$', 'person_creator_wait'),
    # 个人创作管理首页。个人作品列表(草稿)
    (r'^person_creator_new/$', 'person_creator_new'),
    # 个人作品评论管理。作品列表
    (r'^person_creator/remark_manage/$', 'person_creator_remark'),
    # 个人作品评论列表。指定作品的评论列表
    (r'^person_creator/remark_list/$', 'person_creator_remark_list'),
    # 个人作品分类管理
    (r'^person_creator/type_manage/$', 'person_creator_types'),
)

# 增加后台活动比赛创作管理
urlpatterns += patterns(
    'manager2.activity_manage',
    # 活动创建
    (r'^activity/create/$', 'edit_activity'),
    # 活动列表
    (r'^activity/list/$', 'activity_list'),
    # 报名人员列表
    (r'^activity/sign_up_member_list/$', 'activity_sign_up_member_list'),
    # 参与人员列表
    (r'^activity/join_member_list/$', 'activity_join_member_list'),
    # 活动作品管理
    (r'^activity/fruit_list/$', 'activity_fruit_manage'),
    # 结果与新闻管理
    (r'^activity/news/$', 'news_manage'),
    # 结果与新闻编辑
    (r'^activity/news_edit/$', 'news_edit'),
    # 结果与新闻播报查看
    (r'^activity/news_view/$', 'news_view'),
    # 活动背景管理
    (r'^activity/background/$', 'background_manage'),
    # 查看活动作品
    (r'^activity/view_activity_fruit/$', 'view_activity_fruit'),
    # 下载活动的
    (r'^activity/download_activity_join_member/$', 'download_activity_join_member'),
    # 活动创建第一步。
    # editor: kamihati 2015/6/9 新版设计使用分步处理
    (r'^activity/edit_step_1/$', 'edit_activity_step1'),
    # 活动创建第二步
    (r'^activity/edit_step_2/$', 'edit_activity_step2'),
    # 活动概况的系统作品列表（预告通告结果新闻等）
    (r'^activity/info/$', 'activity_info_list'),
    # 活动慨况页面的活动作品列表
    (r'^activity/info_fruit_list/$', 'activity_info_list_fruit'),
    # 浏览活动作品
    (r'^activity/view_fruit/$', 'view_fruit'),
)

# 增加2.0版后台话题相关管理页面和请求的url
urlpatterns += patterns(
    'manager2.topic_manage',
    # 话题管理
    (r'^topic_list/$', 'topic_list'),
    # 评论管理。
    (r'^comment_list/$', 'comment_list'),
    # 话题表情管理
    (r'^topic_emotion/$', 'emotion_manage'),
)

# 学习平台管理配置
urlpatterns += patterns(
    'manager2.study_manage',
    # 图书管理
    (r'^study/book/$', 'book_manage'),
    # 视频管理
    (r'^study/video/$', 'video_manage'),
    # 音频管理
    (r'^study/music/$', 'music_manage'),
    # 游戏管理
    (r'^study/game/$', 'game_manage'),
    # 资源类型管理
    (r'^study/res_type/$', 'res_type_manage'),
    # 资源栏目管理
    (r'^study/res_channel/$', 'res_channel_manage'),
)

# 素材管理url配置
urlpatterns += patterns(
   'manager2.resource_manage',
    # 素材管理首页/公共素材管理
    (r'^resource/$', 'common_resource_manage'),
    # 模板管理
    (r'^resource/template_manage/$', 'template_manage'),
    # 作品尺寸管理
    (r'^resource/size_manage/$', 'size_manage'),
    # 个人素材管理
    (r'^resource/person_manage/$', 'person_resource_manage'),
    # 素材类型管理
    (r'^resource/type_manage/$', 'resource_type_manage'),

    # 远程调用
    # 增加素材类型
    (r'^resource/ajax_create_type/$', 'ajax_create_resource_type'),
    # 修改素材类型
    (r'^resource/ajax_alter_type/$', 'ajax_alter_resource_type'),
    # 增加素材风格
    (r'^resource/ajax_create_style/$', 'ajax_create_resource_style'),
    # 修改素材风格
    (r'^resource/ajax_alter8_style/$', 'ajax_alter_resource_style'),
    # 删除素材类型
    (r'^resource/drop_type/$', 'ajax_drop_type'),
    # 删除素材风格
    (r'^resource/drop_style/$', 'ajax_drop_style'),
)

urlpatterns += patterns(
    'manager2.expert_score_manage',
    # 专家评分管理首页。选择要评分的活动
    (r'^expert_score_manage/$', 'expert_default'),
    # 专家评分页面。对评分首页选择的活动中的作品进行评分
    (r'^expert_score_manage/expert_score/$', 'expert_score'),
    # 专家评分的结果
    (r'^expert_score_manage/score_record/$', 'score_record'),
)

urlpatterns += patterns(
    'manager2.system_manage',
    (r'^system/list_xtxx/$', 'list_xtxx'), #系统消息
    (r'^system/list_lygl/$', 'list_lygl'), #留言管理
    (r'^system/list_jygl/$', 'list_jygl'), #加油站管理
    (r'^system/list_grrz/$', 'list_grrz'), #个人用户操作日志
    (r'^system/list_czrz/$', 'list_manager_log'), #管理员用户操作日志
    (r'^system/m_log_delete/$', 'm_log_delete')#管理员日志,

)


urlpatterns += patterns(
    'manager2.template_manage',
    # 作品模板管理
    (r'^opus_temp/list_mbyc/$', 'template_list'),
    (r'^opus_temp/list_mbzp/$', 'opus_to_template'),
    (r'^opus_temp/list_mbcc/$', 'size_manage'),
)
