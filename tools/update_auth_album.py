#coding: utf-8
'''
Created on 2015年3月12日

@author: Administrator
'''
import os
import sys
sys.path.insert(0, '..')
sys.path.append('/www/webzone/')

#使用django的数据库
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebZone.settings'

from diy.models import AuthAlbum
from diy.models import AuthAsset
import shutil

base_dir = "/www/webzone/media/user/"



class UpdateAuthAlbum():
    def __init__(self):
        for auth_asset in AuthAsset.objects.filter(album_id=0, res_type=1).order_by('user'):
            self.run(auth_asset)
    
    
    def get_default_album(self, user_id):
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
    
    def run(self, auth_asset):
        print auth_asset.id
        auth_album = self.get_default_album(auth_asset.user_id)
        if not auth_album:
            print "error auth_album:", auth_asset.id
        else:
            user_path = "%d/%s/%d/image" % (auth_asset.user.library_id, auth_asset.user.date_joined.strftime("%Y"), auth_asset.user_id)
            source_path = os.path.join(base_dir, "%s/0" % user_path)
            dest_path = os.path.join(base_dir, "%s/%d" % (user_path, auth_album.id))
            print "source_path:", source_path, "dest_path:", dest_path
            #return
            if os.path.exists(source_path):
                shutil.move(source_path, dest_path)
            
            auth_asset.album_id = auth_album.id
            auth_asset.res_path = auth_asset.res_path.replace("/0/", "/%d/" % auth_album.id)
            auth_asset.img_large_path = auth_asset.img_large_path.replace("/0/", "/%d/" % auth_album.id)
            auth_asset.img_medium_path = auth_asset.img_medium_path.replace("/0/", "/%d/" % auth_album.id)
            auth_asset.img_small_path = auth_asset.img_small_path.replace("/0/", "/%d/" % auth_album.id)
            auth_asset.save()
    



if __name__ == "__main__":
    for auth_asset in AuthAsset.objects.filter(res_type=1, user_id=15).order_by('user'):
        auth_asset.res_path = auth_asset.res_path.replace("/image/%d/" % auth_asset.id, "/image/%d/" % auth_asset.album_id)
        auth_asset.img_large_path = auth_asset.img_large_path.replace("/image/%d/" % auth_asset.id, "/image/%d/" % auth_asset.album_id)
        auth_asset.img_medium_path = auth_asset.img_medium_path.replace("/image/%d/" % auth_asset.id, "/image/%d/" % auth_asset.album_id)
        auth_asset.img_small_path = auth_asset.img_small_path.replace("/image/%d/" % auth_asset.id, "/image/%d/" % auth_asset.album_id)
        auth_asset.save()
            
    #UpdateAuthAlbum()






