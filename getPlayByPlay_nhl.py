#!/usr/bin/env python

import os, sys, glob
import re
import datetime

start3 = [2005, 12, 1]
end3 = [2013, 12, 31]
dt = 7

schDir = './season_gids_files'
pbpDir = './play_by_play_files'

###################
def getListOfGids(gfile):
    gids = []
    lines = [l.strip() for l in open(gfile).readlines()]
    for l in lines:
        if len(l)<1:
            continue
        gids.append(l.split()[0])
    return gids

###################
def getSchedFile(year, mn, day):
    url = 'http://espn.go.com/nhl/schedule/_/date/%d%02d%02d' % (year, mn, day)
    ofile = '%s/sch%d%02d%02d.html' % (schDir, year, mn, day)
    cmd = 'wget -O %s %s ' % (ofile, url)
    if not os.path.exists(ofile):
        print cmd
        os.system(cmd)
    return ofile

###################
def getGids(gfile, sfs):
    gids = getListOfGids(gfile)

    for sf in sfs:
        if os.path.exists(sf):
            print 'sf', sf
            tgids = parseSchedFile(sf)
            print 'tgids', tgids
            for t in tgids:
                if not t in gids:
                    gids.append(t)

    ofp = open(gfile, 'w')
    for g in gids:
        ofp.write('%d\n' % int(g))
    ofp.close()

    return gids

###################
def parseSchedFile(f):
    gids = []
    print 'file= ', f
    lines = [l.strip() for l in open(f).readlines()]
    for l in lines:
        if len(l)<=1:
            continue
        tmp = l.split('<td>')

        for t in tmp:
            t = t.replace('\"', '')
            m = re.search('gameId=([0-9]+)>', t)
            if m:
                print t, m.group(1)
                gids.append(m.group(1))
    return gids

###################
def getPlayByPlayFile(gid):
    ofile = '%s/gid%d.html' % (pbpDir, int(gid))
    print 'ofile= ', ofile
    url = 'http://sports.espn.go.com/nhl/playbyplay\?gameId=%d\&period=0' % int(gid)
    cmd = 'wget -O %s %s' % (ofile, url)
    if not os.path.exists(ofile):
        print 'cmd= ', cmd
        os.system(cmd)
    else:
        print 'ofile %s already exists! skip!' % ofile

###################
def getBoxScoreFile(gid):
    ofile = '%s/box%d.html' % (pbpDir, int(gid))
    print 'ofile= ', ofile
    url = 'http://sports.espn.go.com/nhl/boxscore\?gameId=%d' % int(gid)
    cmd = 'wget -O %s %s' % (ofile, url)
    if not os.path.exists(ofile):
        print 'cmd= ', cmd
        os.system(cmd)
    else:
        print 'ofile %s already exists! skip!' % ofile

###################
def parseBoxScoreFile(f):
    data = []
    print 'file= ', f
    lines = [l.strip() for l in open(f).readlines()]
    isum = False
    idata = 0

    igo = False
    for l in lines:
#        print l
        if len(l)<=1:
            continue

        if 'Summary' in l:
            if not 'Period' in l:
                continue
            isum = True
            m = re.search('>(.+)Summary', l)
            ans = m.group(1)
            sper = ans.split('>')[-1]
            print l, sper
            if '1st' in sper:
                per = 1
            elif '2nd' in sper:
                per = 2
            elif '3rd' in sper:
                per = 3
            elif 'OT' in sper:
                per = -1
            else:
                raise Exception

        if not isum:
            continue

        st1 = l.split('</tr>')
        for s1 in st1:
            st2 = s1.split('</td>')
            for s2 in st2:
                print 's2', s2
                if 'Scoring' in s2 and 'Detail' in s2:
                    igo = True
                    print 'Go!'
                if 'Penalty' in s2 and 'Detail' in s2:
                    igo = False
                    print 'Stop!'
                if not igo:
                    continue
                if '</thead' in s2:
                    ii = 0
                    tim = s2.split('>')[-1]
                if '<tr' in s2:
                    ii = 0
                    tim = s2.split('>')[-1]
                if '<td' in s2:
                    ii += 1
                    print 'ii', ii
                    if ii==3:
                        print s2
                        print s2.split('>')[-1]
                        vis = int(s2.split('>')[-1])                        
                    if ii==4:
                        home = int(s2.split('>')[-1])
                        data.append([tim, vis, home] + sv)
    return data

###################
def parseHomeAway(l):
    data = []
#    ofp = open('blah', 'a')
    if not 'totalScoreHome' in l:
        return None

    testy = ['lsAway', 'lsHome']
    tStrings = []
    st = l.split('class')
    for s in st:
#        print '**********'
#        print s
#        ofp.write('********\n')
#        ofp.write('%s\n' % s)

        for itest, test in enumerate(testy):
            if test in s:
                tt = s.split('</td>')
                for t in tt:
                    t = t.replace('</a>','')
                    ans = t.split('>')[-1]
                    ans = ans.replace(' ', '')                    
                    if 'team' in t:
                        data.append(ans)
                        tStrings.append(t)
                    elif (test + str(1)) in t:
                        if len(ans)==0:
                            ans = 0
                        data.append(int(ans))
                    elif (test + str(2)) in t:
                        if len(ans)==0:
                            ans = 0
                        data.append(int(ans))
                    elif (test + str(3)) in t:
                        if len(ans)==0:
                            ans = 0
                        data.append(int(ans))
                    print t

#    ofp.close()
    return data, tStrings[0], tStrings[1]

###################
def parsePlayByPlayFile(f):
    data = []
    gids = []
    print 'file= ', f
    lines = [l.strip() for l in open(f).readlines()]
    isum = False
    idata = 0
    ishoot = False
    scores = [0, 0]
    for l in lines:

        if len(l)<=1:
            continue

        v = parseHomeAway(l)
        if not v is None:
            sv = v[0]
            v = list(v)
            for iv in range(1, 1+2): 
                t = v[iv]
                t = t.replace('-', '')
                t = t.replace(' ', '')
                t = t.lower()
                t = t.replace('newyork','ny')
                v[iv] = t

            awayString = v[1]
            homeString = v[2]

        if 'Summary' in l:
            isum = True
            m = re.search('>(.+)Summary', l)
            ans = m.group(1)
            sper = ans.split('>')[-1]
            sper = sper.replace(' ','')
            print 'sper', sper
            if sper=='Shootout':
                ishoot = True
            if '1st' in sper:
                per = 1
            elif '2nd' in sper:
                per = 2
            elif '3rd' in sper:
                per = 3
            else:
                per = -1

        if ishoot:
            continue

        if not isum:
            continue

        tmp = l.split('<tr>')
#        print 'tmp', tmp

        for t in tmp:
            if not 'width' in t:
                continue
            if 'colspan' in t:
                continue

            m = re.search('<td(.+)</td>', t)
            if m:
#                print t
                ans = m.group(1)
#                print 'ans0', ans
                ans = ans.replace('</span>','')
                ans = ans.replace('</b>','')
                ans = ans.split('>')[-1]
#                print idata, ans
                
                if idata==0:
#                    print 'ans', ans
                    if per>0:
                        st = ans.split(':')
                        mn = int(st[0])
                        sc = int(st[1])
                    else:
                        mn = sc = -1
                if idata==1:
                    tm = ans
                if idata==2:
                    desc = ans
                    desc = desc.replace(',',' ')
                    tmp = [per, mn, sc, tm, desc]
                    if per<0:
                        iHome = 'OT'
                        iHome = -1
                    else:
#                        print 'tm', tm
#                        print 'away', awayString.lower()
#                        print 'home', homeString.lower()
                        test = tm.lower()
                        test = test.replace(' ','')
                        test = test.replace('.','')
                        if test in awayString:
                            iHome = 'away'
                            iHome = 0
                        elif test in homeString:
                            iHome = 'home'
                            iHome = 1
                        else:
                            raise Exception
                    if 'scored' in desc.lower():
                        iscore = 1
                        dsc = scores[1]-scores[0]
                        if per>0:
                            scores[iHome] += 1
                    else:
                        iscore = 0
                        dsc = scores[1]-scores[0]
                    data.append(tmp + sv + [iHome, scores[0], scores[1], iscore, dsc])
                idata += 1
                idata = (idata % 3)
    return data

###################
if __name__=='__main__':
#    fs = glob.glob('./season_gids_files/sch*html')

    gfile = 'listOfGids.txt'

    ingid = None
    for ia, a in enumerate(sys.argv):
        if a=='-gid':
            ingid = int(sys.argv[ia+1])

    if not ingid is None:
        pfile = '%s/gid%d.html' % (pbpDir, int(ingid))
        pbp = parsePlayByPlayFile(pfile)
        for d in pbp:
            print d
        sys.exit()

    stime = datetime.date(start3[0], start3[1], start3[2])
    etime = datetime.date(end3[0], end3[1], end3[2])
    to = stime.toordinal()
    eto = etime.toordinal()

    sfs = []
    while to<=eto:
        tdate = datetime.date.fromordinal(to)
        print to, eto, tdate
        to += dt
        sf = getSchedFile(tdate.year, tdate.month, tdate.day)
        sfs.append(sf)

    gids = getGids(gfile, sfs)

    for gid in gids:
        getPlayByPlayFile(gid)
#        getBoxScoreFile(gid)
    
    gid = gids[0]
    pfile = '%s/gid%d.html' % (pbpDir, int(gid))
    bfile = '%s/box%d.html' % (pbpDir, int(gid))

    veto = [280127031
            ,290125031
            ,310130073
            ,400215960
            ]

    ofp = open('nhlPlayByPlay.csv','w')
    ofp.write('gid,per,mn,sec,tm,decript,away,a1,a2,a3,home,h1,h2,h3,ihome,ascore,hscore,iscore,dsc\n')
    for gid in gids:
        if int(gid) in veto:
            continue
        pfile = '%s/gid%d.html' % (pbpDir, int(gid))
        bfile = '%s/box%d.html' % (pbpDir, int(gid))
        pbp = parsePlayByPlayFile(pfile)
#    pbp = parseBoxScoreFile(bfile)
        for d in pbp:
            print d
            ofp.write('%d,' % int(gid))
            for k in d[0:-1]:
                ofp.write('%s,' % str(k))
            k = d[-1]
            ofp.write('%s\n' % str(k))
