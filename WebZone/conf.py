#coding: utf-8
'''
Created on 2014-3-24

@author: Administrator
'''
QUESTION = {1:"您母亲的姓名是？",
            2:"您父亲的姓名是？",
            3:"您喜欢的偶像名字是？",
            4:"您母亲的生日是？",
            5:"您父亲的生日是？",
            6:"您喜欢的偶像生日是？",
            7:"您最好的朋友名字是？",
            }

#缩略图的尺寸
THUMBNAIL_SIZE = (240, 190)

MEMCACHED_ADDR = "127.0.0.1:11211"

AUTH_TYPE_CHOICES = ((0, u'普通会员'), (1, u'机构管理员'), (2, u'机构普通管理员'), (5, u'游客会员'),(8, u'二级管理员'),  (9, u'超级管理员'), (11, u'故事大王会员'))

fonts = {1:{"label":u"微软雅黑","font":u"微软雅黑.ttf","img":u"微软雅黑.jpg"},
         2:{"label":u"华康少女文字","font":u"华康少女文字.ttf","img":u"华康少女文字.jpg"},
         3:{"label":u"方正卡通简体","font":u"方正卡通简体.ttf","img":u"方正卡通简体.jpg"},
         4:{"label":u"华康娃娃体","font":u"华康娃娃体.ttf","img":u"华康娃娃体.jpg"},
         5:{"label":u"迷你简萝卜","font":u"迷你简萝卜.ttf","img":u"迷你简萝卜.jpg"},
         6:{"label":u"迷你简幼线","font":u"迷你简幼线.ttf","img":u"迷你简幼线.jpg"},
         7:{"label":u"方正少儿简体","font":u"方正少儿简体.ttf","img":u"方正少儿简体.jpg"},
         8:{"label":u"华康海报体","font":u"华康海报体.ttf","img":u"华康海报体.jpg"},
         9:{"label":u"汉仪菱心体简","font":u"汉仪菱心体简.ttf","img":u"汉仪菱心体简.jpg"},
         10:{"label":u"经典趣体简","font":u"经典趣体简.ttf","img":u"经典趣体简.jpg"},
         11:{"label":u"方正喵呜体","font":u"方正喵呜体.ttf","img":u"方正喵呜体.jpg"},
         12:{"label":u"方正超粗黑简体","font":u"方正超粗黑简体.ttf","img":u"方正超粗黑简体.jpg"},
         13:{"label":u"方正粗活意简体","font":u"方正粗活意简体.ttf","img":u"方正粗活意简体.jpg"},
         14:{"label":u"方正彩云繁体","font":u"方正彩云繁体.ttf","img":u"方正彩云繁体.jpg"},
         15:{"label":u"方正剪纸简体","font":u"方正剪纸简体.ttf","img":u"方正剪纸简体.jpg"},
         16:{"label":u"方正小标宋简体","font":u"方正小标宋简体.ttf","img":u"方正小标宋简体.jpg"},
         17:{"label":u"方正行楷简体","font":u"方正行楷简体.ttf","img":u"方正行楷简体.jpg"},
         18:{"label":u"叶友根钢笔行书","font":u"叶友根钢笔行书.ttf","img":u"叶友根钢笔行书.jpg"},
         19:{"label":u"汉真广标","font":u"汉真广标.ttf","img":u"汉真广标.jpg"},
         }

new_fonts = [
     {'id': 20, 'label': u'0001', 'img': '', 'icon': '0001_s.png', 'rect': '', 'size': 22 },
     {'id': 21, 'label': u'0002', 'img': u'0002_b.png', 'icon': '0002_s.png', 'rect': '55.95,31.60,258.30,137.3', 'size': 22 },
]

#充许上传的图片的扩展名
ALLOWED_IMG_EXTENSION = ['.jpg','.jpeg','.png','.gif','.bmp','.swf']
ALLOWED_IMG_UPLOAD_SIZE = 1024*1024*10    #最大上传10M的图片文件
#充许上传的声音资料的扩展名
ALLOWED_SOUND_EXTENSION = ['.mp2','.mp3','.mp4','.ac3','.au']
ALLOWED_SOUND_UPLOAD_SIZE = 1024*1024*10    #最大上传10M的声音文件
#充许上传的视频资料的扩展名
ALLOWED_VIDEO_EXTENSION = ['.mp2','.mp4','.mpeg','.mpg','.3gpp','.flv','.mov','.dvix','.dv','.vob','.3gp','.wmv','.avi','.vob','.mts','.m2ts','.mxf','.f4v','.m4v','.mkv']
ALLOWED_VIDEO_UPLOAD_SIZE = 1024*1024*1024*2    #最大上传2G的视频文件


#["background", "decorator", "frame", "template"]
ZONE_RES_TYPE = {1:u"背景",
                 2:u"装饰",
                 3:u"画框",
                 4:u"模板",
                 5:u"声音",
                 6:u"视频",
                 7:u"图片",
                 8:u"特效",
                 
                 10:u"话题模板",
                 11:u"话题标签",
                 12:u"话题表情",
                 }
ZONE_RES_TYPE_CHOICES = ((1,u"背景"),(2,u"装饰"),(3,u"画框"),(4,u"模板"),(5,u"声音"),(6,u"视频"),(7,u"图片"),(8,u"特效"),(10,u"话题模板"),(11,u"话题标签"),(12,u"话题表情"))


#话题分类
TOPIC_TYPE_CHOICES = ((1,u"动漫"),(2,u"电影"),(3,u"音乐"),(4,u"教育"),(5,u"文学"),(6,u"娱乐"),(7,u"新鲜事"))
TOPIC_TYPE_INSERT=((1,u"表情"),(2,u"图片"),(3,u"音频"),(4,u"视频"),(5,u"作品"))
#表情分类
ZONE_EMOTION = {1:{"id":1,"name":u"默认","normal":"", "hot":""},
                2:{"id":1,"name":u"默认","normal":"", "hot":""},
                }
ZONE_EMOTION_CHOICES = ((1,u"默认"), (2,u"蘑菇头"))

ZONE_RES_STYLE = {1:u"复古",
                  2:u"简约",
                  #3:u"非主流",
                  4:u"可爱",
                  5:u"手绘",
                  6:u"中国风",
                  #7:u"现代",
                  #8:u"小清新",
                  9:u"卡通",
                  #10:u"插画",
                  #11:u"文字",
                  12:u"节日",
                  }
ZONE_RES_STYLE_CHOICES = ((1,u"复古"),(2,u"简约"),(4,u"可爱"),(5,u"手绘"),(6,u"中国风"),(9,u"卡通"),(12,u"节日"))

ZONE_SOUND_STYLE = {1:u"短声音",
                  2:u"长声音",
                  3:u"非主流",
                  }

ZONE_VIDEO_STYLE = {1:u"短声音",
                  2:u"长声音",
                  3:u"非主流",
                  }

#个人资源的类型
PERSONAL_RES_TYPE = {1:u"图片",
                     2:u"声音",
                     3:u"视频",
                     4:u"涂鸦",
                     
                     11:u"故事大王",
                     }
PERSONAL_RES_TYPE_CHOICES = ((1,u"图片"),(2,u"声音"),(3,u"视频"),(4,u"涂鸦"),(11,u"故事大王"))


#作品显示类型不同的分类
OPUS_SHOW_TYPE = {0:u"默认分类",
                  101:u"故事大王大赛"}

SHOW_TYPE_CHOICES = ((0,u"默认分类"),(101,u"故事大王大赛"))

#个人作品分类
OPUS_TYPE = {1:u"文学创作",
             2:u"才艺展示",
             3:u"成长点滴",
             4:u"话题互动",
             }

# OPUS_TYPE = {1:{"name":u"写作","class":{11,u"asdfsd"}},
#              2:u"才艺",
#              3:u"微生活",
#              4:u"即时创作",
#              }

#个人作品分类
OPUS_TYPE_CHOICES = ((1,u"文学创作"),(2,u"才艺展示"),(3,u"成长点滴"),(4,u"话题互动"))

#作品子分类
OPUS_CLASS = {100:u"默认",
              101:u"书信",
              102:u"作文",
              103:u"日记",
              
              200:u"默认",
              201:u"书法",
              202:u"绘画",
              203:u"歌舞",
              204:u"讲故事",
              205:u"诵读",
              
              212:u"故事大王",
              
              300:u"默认",
              301:u"毕业纪念册",
              302:u"旅游笔记本",
              303:u"节日纪念册",
              304:u"亲子照片书",
              305:u"卡片",
              
              400:u"默认",
              401:u"说说",
              402:u"奇葩",
              }


OPUS_CLASS_CHOICES = ((101,u"书信"),(102,u"作文"),(103,u"日记"),
              
              (201,u"书法"),(202,u"绘画"),(203,u"歌舞"),(204,u"讲故事"),(205,u"诵读"),
              
              (301,u"毕业纪念册"),(302,u"旅游笔记本"),(303,u"节日纪念册"),(304,u"亲子照片书"),(305,u"卡片"),
              
              (401,u"说说"),(402,u"奇葩"))


OPUS_STATUS_CHOICES = ((-3,u"创建失败"),(-2,u"删除标记"),(-1,u"审核未通过"),(0,u"草稿"),(1,u"待审核"),(2,u"已表中"))

OPUS_SIZE = ((1, u"921*673：26x19（3071x2245）", (921, 673), (26, 19), (3071, 2245)),
             (2, u"673*921：19x26（2245x3071）", (673, 921), (19, 26), (2245, 3071)),
             (3, u"730*503：20.6x14.2（2433x1677）", (730, 503), (20.6, 14.2), (2433, 1677)),
             (4, u"503*730：14.5x21（1677x2433）", (503, 730), (14.5, 21), (1677, 2433)),
             (5, u"673*673：19x19（2244x2244）", (673, 673), (19, 19), (2244, 2244)),
             (6, u"585*355：16.5x10（1949x1181）", (585, 355), (16.5, 10), (1949, 1181)),
             (7, u"355*585：10x16.5（1181x1949）", (355, 585), (10, 16.5), (1181, 1949)),
             (8, u"886*744：25x21（2953x2480）", (886, 744), (25, 21), (2953, 2480)),
             (9, u"744*886：21x25（2953x2480）", (744, 886), (21, 25), (2953, 2480)),
             (10, u"1063*510：30x14.4（3543X1701）", (1063, 510), (30, 14.4), (3543, 1701)),
             )

#个人信息类型相关
AUTH_MSG_TYPE = ((0,u'私聊信息'),(1,u'作品发表'),(2,u'未通过审核'),(3,u'作品被评论'),(4,u'作品被点赞'),(5,u'作品转为草稿'))
AUTH_MSG_STATUS = ((-1,u'审核未通过'),(0,u'待审核'),(1,u'待读'),(2,u'已读'))



#3qdou服务
# DOU_RES_HOST = "http://yh.3qdou.com"
DOU_RES_HOST = "http://127.0.0.1:8000"
DOU_VIDEO_STREAM_HOST = "http://218.29.68.156:8083/Videos/"   #http://122.0.75.10:8083/Videos/vod/29/31/NFiZI9i3s3pkB/vod_player.swf


#Res_Article: 1
#Res_Books: 2
#Res_Game: 3
#Res_Music: 4
#Res_Picture: 5
#Res_Video: 6
#3qdou资源的类型列表
DOU_ASSET_TYPE = ((0, u"unknow"), (1, u"Article"),(2, u"Books"),(3, u"Game"),(4, u"Music"),(5, u"Picture"),(6, u"Video"))


#活动类型
ACTIVITY_TYPE_CHOICES = ((1,u"学"),(101,u"科普"),(102,u"英语角"),(103,u"阅读"),(104,u"展览"),(105,u"科学活动"),(106,u"其他"),
                         (2,u"玩"),(201,u"影视"),(202),(203,u"游戏"),
                         (3,u"秀"),(301,u"才艺"),(302,u"动手"),
                         (4,u"比"),(401,u"征文"),(402,u"朗诵"),(403,u"歌舞"),(404,u"书法"),(405,u"美术"),(406,u"表演"))

#活动子分类
ACTIVITY_TYPE = {1:u"学",
              101:u"科普",
              102:u"英语角",
              103:u"阅读",
              104:u"展览",
              105:u"科学活动",
              106:u"其他",
              
              2:u"玩",
              201:u"影视",
              202:u"竞猜",
              203:u"游戏",
              
              3:u"秀",
              301:u"才艺",
              302:u"动手",
              
              4:u"比",
              401:u"征文",
              402:u"朗诵",
              403:u"歌舞",
              404:u"书法",
              405:u"美术",
              406:u"表演",
              }



# 后台所有页面权限
# editor: kamihati 2015/5/18
# edit: kamihati 2015/6/16 需求更改后台页面变化
"""
ADMIN_PERMISSION = ['/admin/', '/admin/user/', '/admin/library/', '/admin/old_library/',
                    '/person_creator/', '/person_creator/type_manage/',
                    '/activity/create/', '/activity/list/', '/activity/fruit_list/', '/activity/news/', '/activity/background/',
                    '/topic_list/', '/topic_emotion/',
                    '/study/book/', '/study/video/', '/study/music/', '/study/game/', '/study/res_type/', '/study/res_channel/',
                    '/resource/', '/resource/person_manage/', '/resource/type_manage/',
                    '/expert_score_manage/', '/expert_score_manage/score_record/']
"""
# 总管理员权限
ADMIN_PERMISSION = ['/admin/', '/admin/user/', '/admin/library/', '/admin/old_library/',
                    '/person_creator/', '/person_creator/type_manage/',
                    '/activity/create/', '/activity/list/', '/activity/fruit_list/', '/activity/news/', '/activity/background/', '/activity/info/', '/activity/info_fruit_list/',
                    '/opus_temp/list_mbyc/', '/opus_temp/list_mbzp/', '/resource/size_manage/',
                    '/topic_list/', '/topic_emotion/',
                    '/study/book/', '/study/video/', '/study/music/', '/study/game/', '/study/res_type/', '/study/res_channel/',
                    '/resource/', '/resource/person_manage/', '/resource/type_manage/',
                    '/expert_score_manage/', '/expert_score_manage/score_record/']

# 机构总管理员权限
LIBRARY_ADMIN_PERMISSION = ['/admin/user/', '/admin/library/',
                      '/person_creator/',
                      '/activity/list/', '/activity/info/', '/activity/info_fruit_list/',
                      '/topic_list/',
                      '/resource/person_manage/']