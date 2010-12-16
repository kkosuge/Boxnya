#!/usr/bin/python
#-*- encoding:utf-8 -*-

import time, random
import urllib, urllib2
import hmac, hashlib
import cgi
import simplejson
import re
import hashlib
import yaml
import datetime
from time import sleep , time ,strftime,localtime

class Userstream(object):
    def __init__(self):
        self.ckey = "ZctjpCsuug2VtjfEuceg"
        self.csecret = "pO9WL26Ia9rXyjNavXrit1iclCt1G2J1nRA4jZ6LGc"
        self.reqt_url = 'http://twitter.com/oauth/request_token'
        self.auth_url = 'http://twitter.com/oauth/authorize'
        self.acct_url = 'http://twitter.com/oauth/access_token'
        self._loadOauth()

    def _loadOauth(self):
        try:
            f = open("oauth.yaml","r")
            oauth_dict = yaml.load(f)
            self.atoken = oauth_dict["atoken"]
            self.atoken_secret = oauth_dict["atoken_secret"]
            f.close()
        except IOError:
            print "---> Please authorize Boxnya.\n"
            self.OauthInitializer()

    def _init_params(self):
        p = {
            "oauth_consumer_key": self.ckey,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time())),
            "oauth_nonce": str(random.getrandbits(64)),
            "oauth_version": "1.0"
            }
        return p

    def _make_signature(self, params, url, method, csecret, secret = ""):
        # Generate Signature Base String
        plist = []
        for i in sorted(params):
            plist.append("%s=%s" % (i, params[i]))

        pstr = "&".join(plist)
        msg = "%s&%s&%s" % (method, urllib.quote(url, ""),
                            urllib.quote(pstr, ""))

        # Calculate Signature
        h = hmac.new("%s&%s" % (csecret, secret), msg, hashlib.sha1)
        sig = h.digest().encode("base64").strip()
        return sig

    def OauthInitializer(self):
        # Request Parameters
        params = self._init_params()

        # Generate Signature
        sig = self._make_signature(params, self.reqt_url, "GET", self.csecret)
        params["oauth_signature"] = sig

        # Get Token
        req = urllib2.Request("%s?%s" % (self.reqt_url, urllib.urlencode(params)))
        resp = urllib2.urlopen(req)

        # Parse Token Parameters
        ret = cgi.parse_qs(resp.read())
        token = ret["oauth_token"][0]
        token_secret = ret["oauth_token_secret"][0]

        # Get PIN
        print "* Please access to this URL, and allow."
        print "%s?%s=%s" % (self.auth_url, "oauth_token", token)
        print "\n* After that, will display 7 digit PIN, input here."
        print "PIN ->",
        pin = raw_input()
        pin = int(pin)

        print "Get access token:",

        # Generate Access Token Request
        params = self._init_params()
        params["oauth_verifier"] = pin
        params["oauth_token"] = token

        sig = self._make_signature(params, self.acct_url, "GET", self.csecret, token_secret)
        params["oauth_signature"] = sig

        # Get Access Token
        req = urllib2.Request("%s?%s" % (self.acct_url, urllib.urlencode(params)))
        resp = urllib2.urlopen(req)

        print "\t[OK]\n"

        # Parse Access Token
        fin = cgi.parse_qs(resp.read())
        self.atoken = fin["oauth_token"][0]
        self.atoken_secret = fin["oauth_token_secret"][0]

        oauth_dict = {"atoken":self.atoken, "atoken_secret":self.atoken_secret}
        f = open("oauth.yaml","w")
        yaml.dump(oauth_dict, f, encoding="utf8", default_flow_style=False)
        f.close()

        print "* Done."

    def _oauth_header(self, params):
        plist = []
        for p in params:
            plist.append('%s="%s"' % (p, urllib.quote(params[p])))
        return "OAuth %s" % (", ".join(plist))

    def getStream(self):
        url ='https://userstream.twitter.com/2/user.json'
        params = self._init_params()
        params["oauth_token"] = self.atoken

        sig = self._make_signature(params, url, "GET", self.csecret, self.atoken_secret)
        params["oauth_signature"] = sig

        req = urllib2.Request(url)
        req.add_header("Authorization", self._oauth_header(params))
        return urllib2.urlopen(req)

class IMKayac(object):
    def __init__(self,id,password=None,sig=None):
        self.id = id
        self.password = password
        self.sig = sig

    def notify(self,msg):
        if isinstance(msg, unicode): msg = msg.encode('utf-8')
        path = 'http://im.kayac.com/api/post/%s' % self.id
        params = { 'message':msg, }
        if self.password:
            params['password'] = self.password
        if self.sig:
            params['sig'] = hashlib.sha1(msg+self.sig).hexdigest()
        urllib2.build_opener().open(path, urllib.urlencode(params))

class Boxnya(object):
    def __init__(self):
        self.screen_name = ""
        self.reg_exp = ""
        self.im_id = ""
        self.im_pswd = ""
        self.im_sig = ""
        self._loadSettings()

    def _loadSettings(self):
        try:
            f = open("settings.yaml","r")
            settings = yaml.load(f)
            self.screen_name = settings["screen_name"]
            self.reg_exp = settings["reg_exp"]
            self.im_id = settings["im_id"]
            self.im_pswd = settings["im_pswd"]
            self.im_sig = settings["im_sig"]
            f.close()
        except IOError:
            print "Please set your account data.\n"
            self.SettingsInitializer()

    def SettingsInitializer(self):
        print "* Please input screen name."
        self.screen_name = raw_input("->")
        print "* Please input search keyword. (You can use a regular expression.)"
        self.reg_exp = raw_input("->").decode("utf_8")
        print "* Please input im.kayac userid."
        self.im_id = raw_input("->")
        print "* Please input im.kayac password. (optional)"
        self.im_pswd = raw_input("->")
        print "* Please input im.kayac private key. (optional)"
        self.im_sig = raw_input("->")
        settings_dict = {"screen_name":self.screen_name,
                         "reg_exp":self.reg_exp,
                         "im_id":self.im_id,
                         "im_pswd":self.im_pswd,
                         "im_sig":self.im_sig
                         }
        f = open("settings.yaml","w")
        yaml.dump(settings_dict, f, encoding="utf8", default_flow_style=False)
        f.close()

    def _output(self, text, im):
        im.notify(text)
        time = datetime.datetime.today()
        print "---> ( " + str(time)[:22] + " ) " + text

    def main(self):
        im = IMKayac(self.im_id, self.im_pswd, self.im_sig)
        pattern = re.compile(self.reg_exp + "|@%s" % self.screen_name)
        userstream = Userstream()
        print "---> Boxnya service start"
        stream = userstream.getStream()
        stream.readline()
        stream.readline()
        while True:
            recv = stream.readline()
            try:
                json = simplejson.loads(recv)
            except simplejson.JSONDecodeError:
                pass
            else:
                if json.get("event") == "favorite" and json.get("target")["screen_name"] == self.screen_name:
                    text = u"★ "+ json["source"]["screen_name"] + " Favorited: " + json["target_object"]["text"]
                    self._output(text,im)
                elif pattern.search(json.get("text","")):
                    text = json["user"]["screen_name"] + ": " + json["text"]
                    self._output(text,im)

if __name__ == "__main__":
    try:
        boxnya = Boxnya()
        boxnya.main()
    except KeyboardInterrupt:
        print "\n---> see you !"
