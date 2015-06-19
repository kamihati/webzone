from online_status.status import OnlineStatus

def encode_json(obj):
    def status_name(s):
        if s == 0:
            return 'idle'
        elif s == 1:
            return 'active'
        else:
            return 'error'
    if isinstance(obj, OnlineStatus):
        #seen = obj.seen.isoformat()
        seen = obj.seen.strftime("%Y-%m-%d %H:%M:%S")
        user = {'username': obj.user.username, 'nickname': obj.user.nickname, 'realname': obj.user.realname,}  
        return {'user': user, 'seen': seen, 'status': status_name(obj.status), 'ip': obj.ip,}
    else:
        raise TypeError(repr(obj) + " is not JSON serializable")
