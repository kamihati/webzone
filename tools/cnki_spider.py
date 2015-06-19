#coding: utf-8
'''
Created on 2014-4-30

@author: Administrator
'''
from BeautifulSoup import BeautifulSoup
import requests
from datetime import datetime
import urllib
import time
import sqlite3
import os

#http://epub.cnki.net/kns/brief/brief.aspx?curpage=10&RecordsPerPage=20&
# QueryID=4&ID=&turnpage=1&tpagemode=L&
# dbPrefix=SCDB&Fields=&DisplayMode=listmode&
# PageName=ASP.brief_result_aspx

class spider():
    def __init__(self):
        self.username = "zhangtl8"
        self.password = "xryy114"
        self.islogin = ""
        self.__VIEWSTATE = "/wEPDwUKMTAyNDc0NDMyNmRkgedI29f1SPtvcCpViyyWOJxA1kw="
        self.login_url = "http://epub.cnki.net/kns/logindigital.aspx"
        self.referer = "http://epub.cnki.net/kns/logindigital.aspx?ParentLocation=/kns"
        self.host = "epub.cnki.net"
        self.query_url = "http://epub.cnki.net/kns/brief/brief.aspx?curpage=%d&RecordsPerPage=20&QueryID=4&ID=&turnpage=1&tpagemode=L&dbPrefix=SCDB&Fields=&DisplayMode=listmode&PageName=ASP.brief_result_aspx"
        self.cookie = ""
        self.user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36"
        #self.search_content = u"KY='李斯'-'李斯特'-'李斯杆菌'"
        #self.page_count = 81
        self.search_content = u"KY='重阳节'"
        self.page_count = 123
        self.page_index = 1
        
        self.search1 = "http://epub.cnki.net/KNS/request/SearchHandler.ashx?action=&NaviCode=*&ua=1.21&PageName=ASP.brief_result_aspx&DbPrefix=SCDB&DbCatalog=%s&ConfigFile=SCDB.xml&db_opt=%s&expertvalue=%s&his=0&__=%s"
        self.search = "http://epub.cnki.net/kns/brief/brief.aspx?pagename=ASP.brief_result_aspx&dbPrefix=SCDB&dbCatalog=%s&ConfigFile=SCDB.xml&research=off&t=%s&keyValue=&S=1"
#         self.init_db()
#         result = self.query()
#         while result == "error":
#             print "query restart again"
#             result = self.query()
#         print result
        
#         self.update()
#         return
    
        result = self.update_brief()
        while result == "error":
            print "update_brief restart again"
            result = self.update_brief()
        print result
        print "over over over"

    def init_db(self):
        BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        db_path = os.path.join(BASE_DIR, "cnki.db")
        print db_path
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        #sql = "create table cnki_down(id integer primary key autoincrement, title varchar(255), href varchar(255), brief varchar(8000), author varchar(255), organization varchar(255), keyword varchar(255), download_url varchar(255), times integer default 0, status integer default 0, page_index integer default 0, row_index integer default 0)"
        sql = "create table cnki_99(id integer primary key autoincrement, title varchar(255), href varchar(255), brief varchar(8000), author varchar(255), organization varchar(255), keyword varchar(255), download_url varchar(255), times integer default 0, status integer default 0, page_index integer default 0, row_index integer default 0)"
        cur.execute(sql)
        conn.commit()
        conn.close()
        
    def update(self):
        BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        db_path = os.path.join(BASE_DIR, "cnki.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        DbCatalog = u"中国学术文献网络出版总库"
        db_opt = "CJFQ,CJFN,CDFD,CMFD,CPFD,IPFD,CCND,CCJD,HBRD"
        url = self.search1 % (urllib.quote(DbCatalog.encode("utf-8")), urllib.quote(db_opt.encode("utf-8")), urllib.quote(self.search_content.encode("utf-8")), urllib.quote(datetime.now().strftime("%a %b %d %Y %H:%M:%S GMT+0800")))
        #print url
        s = requests.Session()
        r = s.get(url)
        #print r.text
        url = self.search % (urllib.quote(DbCatalog.encode("utf-8")), str(int(time.time()*1000)))
        print url
        r = s.get(url)
        #print r.text
        f = open("c:\\1.html", "w")
        f.write(r.text)
        f.close()
        
        sql = "select page_index from cnki_99 GROUP BY page_index"
        page_list = range(1, self.page_count+1)
        cur.execute(sql)
        rows = cur.fetchall()
        for row in rows:
            print int(row[0])
            page_list.remove(int(row[0]))
        print page_list
        page_index = page_list.pop()
        while len(page_list) >= 0:
            url = self.query_url % page_index
            print url
            r = s.get(url)
            
            soup = BeautifulSoup(r.text)
            try: tr_list = soup.find('table',{'class':'GridTableContent'}).findAll('tr')
            except:
                print r.text
                time.sleep(10)
                continue
            i = 1
            while i<len(tr_list):
                td_list = tr_list[i].findAll('td')
                href = td_list[1].a['href']
                t = td_list[1].a.text
                title = t[t.find("'")+1:t.rfind("'")]
                title = title.replace("'", "").replace("\\", "")
                author = ""
                for a in td_list[2].findAll('a'):
                    author += ";" + a.text if len(author)>0 else a.text
                #source = td_list[3]
                #press_date = td_list[4]
                #db_name = td_list[5].text
                #press_date = td_list[6].text
                download_url = td_list[7].a['href']
                try: download_times = td_list[7].span.text
                except: download_times = 0
                sql = "insert into cnki_99(title,href,author,download_url,times,page_index,row_index) values('%s','%s','%s','%s',%s,%s,%s)"
                sql = sql % (title, href, author, download_url, download_times, page_index, i)
                print sql
                cur.execute(sql)
                conn.commit()
                i += 1
            page_index = page_list.pop()
        conn.close()
    
    def query(self):
        BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        db_path = os.path.join(BASE_DIR, "cnki.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        DbCatalog = u"中国学术文献网络出版总库"
        db_opt = "CJFQ,CJFN,CDFD,CMFD,CPFD,IPFD,CCND,CCJD,HBRD"
        url = self.search1 % (urllib.quote(DbCatalog.encode("utf-8")), urllib.quote(db_opt.encode("utf-8")), urllib.quote(self.search_content.encode("utf-8")), urllib.quote(datetime.now().strftime("%a %b %d %Y %H:%M:%S GMT+0800")))
        #print url
        s = requests.Session()
        r = s.get(url)
        #print r.text
        url = self.search % (urllib.quote(DbCatalog.encode("utf-8")), str(int(time.time()*1000)))
        print url
        r = s.get(url)
        #print r.text
        f = open("c:\\1.html", "w")
        f.write(r.text)
        f.close()
        
        while self.page_index <= self.page_count:
            url = self.query_url % self.page_index
            print url
            r = s.get(url)
            
            soup = BeautifulSoup(r.text)
            try: tr_list = soup.find('table',{'class':'GridTableContent'}).findAll('tr')
            except:
                print r.text
                time.sleep(10)
                self.page_index += 1
                conn.close()
                return "error"
            i = 1
            while i<len(tr_list):
                td_list = tr_list[i].findAll('td')
                href = td_list[1].a['href']
                t = td_list[1].a.text
                title = t[t.find("'")+1:t.rfind("'")]
                title = title.replace("'", "").replace("\\", "")
                author = ""
                for a in td_list[2].findAll('a'):
                    author += ";" + a.text if len(author)>0 else a.text
                #source = td_list[3]
                #press_date = td_list[4]
                #db_name = td_list[5].text
                #press_date = td_list[6].text
                download_url = td_list[7].a['href']
                try: download_times = td_list[7].span.text
                except: download_times = 0
                sql = "insert into cnki_99(title,href,author,download_url,times,page_index,row_index) values('%s','%s','%s','%s',%s,%s,%s)"
                sql = sql % (title, href, author, download_url, download_times, self.page_index, i)
                print sql
                cur.execute(sql)
                conn.commit()
                i += 1
            self.page_index += 1
        conn.close()
        return "ok"
    
    def update_brief(self):
        BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        db_path = os.path.join(BASE_DIR, "cnki.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        sql = "select id,href, page_index from cnki_99 where status=-4 and id>0"
        cur.execute(sql)
        rows = cur.fetchall()
        print len(rows)
        
        DbCatalog = u"中国学术文献网络出版总库"
        db_opt = "CJFQ,CJFN,CDFD,CMFD,CPFD,IPFD,CCND,CCJD,HBRD"
        url = self.search1 % (urllib.quote(DbCatalog.encode("utf-8")), urllib.quote(db_opt.encode("utf-8")), urllib.quote(self.search_content.encode("utf-8")), urllib.quote(datetime.now().strftime("%a %b %d %Y %H:%M:%S GMT+0800")))
        #print url
        s = requests.Session()
        r = s.get(url)
        #print r.text
        url = self.search % (urllib.quote(DbCatalog.encode("utf-8")), str(int(time.time()*1000)))
        #print url
        r = s.get(url)

        for row in rows:
            if not row: continue
            id = row[0]
            href = row[1]
            page_index = row[2]
            referer = self.query_url % page_index
            url = "http://epub.cnki.net" + href
            print id, url
            s.headers["Referer"] = referer
            #r = s.get(url, proxies="https://127.0.0.1:8087")
            r = s.get(url)
            soup = BeautifulSoup(r.text)
            try: brief = soup.find('span',{'id':'ChDivSummary'}).text
            except: brief = ""
            organization = ""
            try:
                for p in soup.find('div',{'class':'author summaryRight'}).findAll('p'):
                    if p.text.find(u"【机构】") >= 0:
                        organization = p.text.replace(u"【机构】", "")
            except:
                pass
                #sql = "update cnki_99 set status=-4 where id=%d" % id
                #print sql
                #cur.execute(sql)
                #conn.commit()
                #continue
                #return "error"
                #time.sleep(10000)
            try: keyword = soup.find('span',{'id':'ChDivSummary'}).text
            except: keyword = ""
            keyword = ""
            try:
                for a in soup.find('span',{'id':'ChDivKeyWord'}).findAll('a'):
                    keyword += ";" + a.text if len(keyword)>0 else a.text
            except:
                print id, "no keyword"
            
            if brief or organization or keyword:
                sql = "update cnki_99 set brief='%s',organization='%s',keyword='%s',status=1 where id=%d" % (brief, organization, keyword, id)
                print sql
                cur.execute(sql)
                conn.commit()
                #time.sleep(2000)
            else:
                sql = "update cnki_99 set status=-1 where id=%d" % id
                print sql
                cur.execute(sql)
                conn.commit()
#                 conn.close()
#                 time.sleep(5)
#                 return "error"
        conn.close()
        return "ok"
        
if __name__ == "__main__":
    spider()