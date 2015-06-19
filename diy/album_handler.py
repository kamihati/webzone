# coding=utf8

from diy.models import AuthAlbum

def get_default_album(user_id):
    #得到某用户的默认相册
    try:
        auth_album = AuthAlbum.objects.get(user_id=user_id, type_id=0, album_title=u"默认相册", status=1)
    except(AuthAlbum.DoesNotExist):
        auth_album = AuthAlbum()
        auth_album.user_id = user_id
        auth_album.type_id = 0  #系统自动生成
        auth_album.album_title = u"默认相册"
        auth_album.status = 1   #可用状态
        auth_album.save()
    except:
        import traceback
        traceback.print_exc()
        auth_album = None
    return auth_album
