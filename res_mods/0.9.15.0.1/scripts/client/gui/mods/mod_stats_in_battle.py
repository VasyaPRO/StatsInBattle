import BigWorld
import game
import Keys

import json, urllib, urllib2, math, os, re, threading, time

from Avatar import PlayerAvatar
from Account import PlayerAccount
from gui import SystemMessages
from gui import InputHandler
from gui.app_loader import g_appLoader
from gui.battle_control.arena_info import getClientArena, getArenaBonusType
from account_helpers.settings_core.SettingsCore import g_settingsCore
from gui.Scaleform.daapi.view.battle.stats_form import _StatsForm
from gui.battle_control.battle_arena_ctrl import BattleArenaController
from gui.battle_control.arena_info.ArenaDataProvider import ArenaDataProvider
from gui.Scaleform.Battle import Battle
from gui.Scaleform.daapi.view.battle_loading import BattleLoading
from gui.Scaleform.daapi.view.battle.markers import _VehicleMarker, MarkersManager
from gui import GUI_SETTINGS
from gui.Scaleform import VoiceChatInterface
from gui.battle_control.arena_info.arena_vos import VehicleActions
from gui.battle_control import g_sessionProvider, arena_info
from CTFManager import g_ctfManager
from messenger.gui.Scaleform.BattleEntry import BattleEntry
from constants import AUTH_REALM
from gui.Scaleform.daapi.view.lobby.hangar.Hangar import Hangar
from items.vehicles import VEHICLE_CLASS_TAGS
import nations
from ClientArena import ClientArena

__version__ = '2.0'
__author__ = 'VasyaPRO_2014'

print '[LOAD_MOD] StatsInBattle v%s' % __version__


class Config:
    def __init__(self):
        self.load()
        return

    def __call__(self, path):
        path = path.split("/")
        c = self.config
        for x in path:
            c = c[x]
        return c

    def load(self):
        try:
            file = open('res_mods/configs/StatsInBattle/StatsInBattle.json', 'r')
            f = file.read()
            # Delete comments
            while f.count("/*"):
                f = f.replace(f[f.find("/*"):f.find("*/") + 2 if f.find("*/") + 2 != 1 else len(f)], "")
            while f.count("//"):
                f = f.replace(f[f.find("//"):f.find("\n", f.find("//")) if f.find("\n", f.find("//")) != -1 else len(f)], "")
            cfg = json.loads(f)
            # Check on valid
            cfg['reloadKey']
            cfg['region']
            cfg['applicationID']
            cfg['requestTimeout']
            cfg['allowAnalytics']
            cfg['playersPanel']['enable']
            cfg['playersPanel']['large']['nick']['left']
            cfg['playersPanel']['large']['nick']['right']
            cfg['playersPanel']['large']['vehicle']['left']
            cfg['playersPanel']['large']['vehicle']['right']
            cfg['playersPanel']['medium2']['left']
            cfg['playersPanel']['medium2']['right']
            cfg['playersPanel']['medium']['left']
            cfg['playersPanel']['medium']['right']
            cfg['tab']['enable']
            cfg['tab']['nick']['left']
            cfg['tab']['nick']['right']
            cfg['tab']['vehicle']['left']
            cfg['tab']['vehicle']['right']
            cfg['battleLoading']['enable']
            cfg['battleLoading']['nick']['left']
            cfg['battleLoading']['nick']['right']
            cfg['battleLoading']['vehicle']['left']
            cfg['battleLoading']['vehicle']['right']
            cfg['marker']['enable']
            cfg['marker']['nick']
            cfg['marker']['vehicle']
            cfg['colors']['colorCodes']
            cfg['colors']['colorEFF']
            cfg['colors']['colorWGR']
            cfg['colors']['colorWN7']
            cfg['colors']['colorWN6']
            cfg['colors']['colorWinrate']
            cfg['colors']['colorBattles']
            if not len(cfg['colors']['colorCodes']) == len(cfg['colors']['colorEFF']) == len(cfg['colors']['colorWGR']) == len(cfg['colors']['colorWN7']) == len(cfg['colors']['colorWinrate']) == len(cfg['colors']['colorBattles']):
                raise KeyError
        except IOError:
            showMessage('[StatsInBattle] Cannot open config file (res_mods/configs/StatsInBattle/StatsInBattle.json)', 'red')
            self.loadDefault()
        except (ValueError, KeyError):
            showMessage('[StatsInBattle] Config is not valid.', 'red')
            self.loadDefault()
        else:
            self.config = cfg
            showMessage('[StatsInBattle] Config successfully loaded.', 'green')
        finally:
            file.close()
        return
    
    def reload(self):
        self.load()

        arena = getClientArena()
        if arena is not None:
            ids = [str(pl['accountDBID']) for pl in arena.vehicles.values()]
            if ids != stats.dbIDs: # It is possible only on global map
                stats.loadStats()

        # Redraw players panel and tab
        battle = g_appLoader.getDefBattleApp()
        if battle is not None:
            arenaDP = g_sessionProvider.getCtx().getArenaDP()
            for isEnemy, teamIdx in arenaDP.getTeamIDsIterator():
                battle._Battle__arenaCtrl._updateTeamData(isEnemy, teamIdx, arenaDP, False)

    def loadDefault(self):
        showMessage('[StatsInBattle] Loading default config.', "green")
        self.config = {
            'reloadKey': 'KEY_F9',
            'region': 'ru',
            'applicationID': 'demo',
            'requestTimeout': 5,
            'allowAnalytics': True,
            'playersPanel': {
                'enable': True,
                'large': {
                    'nick': {
                        'left': "<img src='{flag_url}' width='16' height='12'> <font color='#{colorBattles}'>{kb}</font> <font color='#{default_color}'>{nick}</font><br/>",
                        'right': "<font color='#{default_color}'>{nick}</font> <font color='#{colorBattles}'>{kb}</font> <img src='{flag_url}' width='16' height='12'><br/>"
                        },
                    'vehicle': {
                        'left': "<font color='#{colorEFF}'>{eff}</font> <font color='#{colorWinrate}'>{winrate:0.0f}%</font><br/>",
                        'right': "<font color='#{colorWinrate}'>{winrate:0.0f}%</font> <font color='#{colorEFF}'>{eff}</font><br/>"
                        }
                    },
                'medium2': {
                    'left': "<font color='#{colorEFF}'>{eff}</font> <font color='#{colorWinrate}'>{winrate:0.0f}%</font><br/>",
                    'right': "<font color='#{colorWinrate}'>{winrate:0.0f}%</font> <font color='#{colorEFF}'>{eff}</font><br/>"
                    },
                'medium': {
                    'left': "<font color='#{colorEFF}'>{nick}</font><br/>",
                    'right': "<font color='#{colorEFF}'>{nick}</font><br/>"
                    }
            },
            'tab': {
               'enable': True,
               'nick': {
                   'left': "<img src='{flag_url}' width='16' height='12'> {nick}",
                   'right': "{nick} <img src='{flag_url}' width='16' height='12'>"
               },
               'vehicle': {
                   'left': "{kb} {winrate:0.0f}% {eff}",
                   'right': "{eff} {winrate:0.0f}% {kb}"
               }
            },
            'battleLoading': {
               'enable': True,
               'nick': {
                   'left': "{nick}",
                   'right': "{nick}"
               },
               'vehicle': {
                   'left': "{kb} {winrate:0.0f}% {eff}",
                   'right': "{eff} {winrate:0.0f}% {kb}"
               }
            },
            "marker": {
                "enable": True,
                "nick": "{winrate}% {nick}",
                "vehicle": "{eff} {vehicle}"
            },
            'colors': {
                'colorCodes': ['FE0E00', 'FE7903', 'F8F400', '60FF00', '02C9B3', 'D042F3'],
                'colorEFF': [1, 615, 870, 1175, 1525, 1850],
                'colorWGR': [1, 2495, 4345, 6425, 8625, 10040],
                'colorWN7': [1, 495, 860, 1220, 1620, 1965],
                'colorWN6': [1, 460, 850, 1215, 1620, 1960],
                'colorWinrate': [1, 47, 49, 52.5, 58, 65],
                'colorBattles': [1, 2000, 6000, 16000, 30000, 43000]
            }
        }
        return


class Statistics:
    def __init__(self):
        self._vehiclesInfo = None
        self.loadVehiclesInfo()
        self.playersInfo = {}
        self.dbIDs = []
        self._account_info = None
        self._account_tanks = None

    def loadStats(self):
        arena = getClientArena()
        if arena is not None:
            if getArenaBonusType() != 6: # If it isn't tutorial battle
                self.dbIDs = [str(pl['accountDBID']) for pl in arena.vehicles.values()]
                idsStr = ','.join(self.dbIDs)
                account_info = 'https://api.worldoftanks.{region}/wot/account/info/?application_id={appId}&fields=client_language%2Cglobal_rating%2Cstatistics.all.battles%2Cstatistics.all.wins%2Cstatistics.all.damage_dealt%2Cstatistics.all.frags%2Cstatistics.all.spotted%2Cstatistics.all.capture_points%2Cstatistics.all.dropped_capture_points&account_id={id}'.format(id=idsStr, region=config('region'), appId=config('applicationID'))
                account_tanks = 'https://api.worldoftanks.{region}/wot/account/tanks/?application_id={appId}&fields=statistics.battles%2Ctank_id&account_id={id}'.format(id=idsStr, region=config('region'), appId=config('applicationID'))
                #startTime = time.time()
                try:
                    self._account_info = json.loads(urllib2.urlopen(account_info, timeout=config('requestTimeout')).read()).get('data', None)
                    self._account_tanks = json.loads(urllib2.urlopen(account_tanks, timeout=config('requestTimeout')).read()).get('data', None)
                except IOError:
                    showMessage('[StatsInBattle] Error loading statistics.', "red")
                    self._account_info = None
                    self._account_tanks = None
                else:
                    #print "Statistics successfully loaded [%s sec]" % str(time.time()-startTime)
                    for value in arena.vehicles.values():
                        dbID = str(value['accountDBID'])
                        if self._account_info[dbID] and self._account_info[dbID]['statistics']['all']['battles'] != 0:
                            self.playersInfo[dbID] = {}
                            self.playersInfo[dbID]['team'] = value['team']
                            self.playersInfo[dbID]['name'] = value['name']
                            self.playersInfo[dbID]['clan'] = "[%s]" % value['clanAbbrev'] if value['clanAbbrev'] else ""
                            self.playersInfo[dbID]['nick'] = self.playersInfo[dbID]['name'] + self.playersInfo[dbID]['clan']
                            self.playersInfo[dbID]['clannb'] = value['clanAbbrev']
                            self.playersInfo[dbID]['vehicle'] = value['vehicleType'].type.userString
                            self.playersInfo[dbID]['tank_id'] = value['vehicleType'].type.compactDescr
                            self.playersInfo[dbID]['level'] = value['vehicleType'].level
                            self.playersInfo[dbID]['type'] = tuple(value['vehicleType'].type.tags & VEHICLE_CLASS_TAGS)[0]
                            self.playersInfo[dbID]['nation'] = nations.NAMES[value['vehicleType'].type.customizationNationID]
                            self.playersInfo[dbID]['wgr'] = self._account_info[dbID]['global_rating']
                            self.playersInfo[dbID]['battles'] = self._account_info[dbID]['statistics']['all']['battles']
                            self.playersInfo[dbID]['winrate'] = self._account_info[dbID]['statistics']['all']['wins'] * 100.0 / self._account_info[dbID]['statistics']['all']['battles']
                            self.playersInfo[dbID]['kb'] = str(int(round(self._account_info[dbID]['statistics']['all']['battles']/1000, 0))) + 'k' if self._account_info[dbID]['statistics']['all']['battles'] >= 1000 else self._account_info[dbID]['statistics']['all']['battles']
                            self.playersInfo[dbID]['colorWGR'] = self.getColor('colorWGR', self.playersInfo[dbID]['wgr'])
                            self.playersInfo[dbID]['colorBattles'] = self.getColor('colorBattles', self.playersInfo[dbID]['battles'])
                            self.playersInfo[dbID]['colorWinrate'] = self.getColor('colorWinrate', self._account_info[dbID]['statistics']['all']['wins'] * 100.0 / self._account_info[dbID]['statistics']['all']['battles'])
                            self.playersInfo[dbID]['lang'] = self._account_info[dbID]['client_language']
                            self.playersInfo[dbID]['flag_url'] = 'img://scripts/client/gui/mods/mod_stats_in_battle/flags/' + self.playersInfo[dbID]['lang'] + '.png'
                            self.playersInfo[dbID]['spg_battles'] = 0
                            if self._vehiclesInfo is not None:
                                avgDmg = self._account_info[dbID]['statistics']['all']['damage_dealt'] / float(self._account_info[dbID]['statistics']['all']['battles'])
                                avgFrags = self._account_info[dbID]['statistics']['all']['frags'] / float(self._account_info[dbID]['statistics']['all']['battles'])
                                avgSpot = self._account_info[dbID]['statistics']['all']['spotted'] / float(self._account_info[dbID]['statistics']['all']['battles'])
                                avgCap = self._account_info[dbID]['statistics']['all']['capture_points'] / float(self._account_info[dbID]['statistics']['all']['battles'])
                                avgDef = self._account_info[dbID]['statistics']['all']['dropped_capture_points'] / float(self._account_info[dbID]['statistics']['all']['battles'])
                                battles = self._account_info[dbID]['statistics']['all']['battles']
                                winrate = self._account_info[dbID]['statistics']['all']['wins'] * 100.0 / self._account_info[dbID]['statistics']['all']['battles']
                                player_tier_temp = 0
                                for tank in self._account_tanks[dbID]:
                                    if str(tank['tank_id']) in self._vehiclesInfo:
                                        player_tier_temp += self._vehiclesInfo[str(tank['tank_id'])]['level'] * tank['statistics']['battles']
                                        if self._vehiclesInfo[str(tank['tank_id'])]['type'] == "SPG":
                                            self.playersInfo[dbID]['spg_battles'] += tank['statistics']['battles']
                                    else:
                                        description = "ERROR: unknown tank_id %s in player %s" % (tank['tank_id'], dbID)
                                        if self.playersInfo[dbID]['tank_id'] == tank['tank_id']:
                                            player_tier_temp += self.playersInfo[dbID]['level'] * tank['statistics']['battles']
                                            description += " (%s, level %d, type %s, nation %s)" % (self.playersInfo[dbID]['vehicle'], self.playersInfo[dbID]['level'], self.playersInfo[dbID]['type'], self.playersInfo[dbID]['nation'])
                                        ga.send_exception(description)
                                avgTier = float(player_tier_temp) / self._account_info[dbID]['statistics']['all']['battles']
                                self.playersInfo[dbID]['eff'] = self.getEFF(avgDmg, avgTier, avgFrags, avgSpot, avgCap, avgDef)
                                self.playersInfo[dbID]['wn7'] = self.getWN7(avgDmg, avgTier, avgFrags, avgSpot, avgDef, winrate, battles)
                                self.playersInfo[dbID]['wn6'] = self.getWN6(avgDmg, avgTier, avgFrags, avgSpot, avgDef, winrate)
                                self.playersInfo[dbID]['spg_percent'] = float(self.playersInfo[dbID]['spg_battles']) / battles * 100.0
                            else:
                                self.playersInfo[dbID]['eff'] = 0
                                self.playersInfo[dbID]['wn7'] = 0
                                self.playersInfo[dbID]['wn6'] = 0
                            self.playersInfo[dbID]['colorEFF'] = self.getColor('colorEFF', self.playersInfo[dbID]['eff'])
                            self.playersInfo[dbID]['colorWN7'] = self.getColor('colorWN7', self.playersInfo[dbID]['wn7'])
                            self.playersInfo[dbID]['colorWN6'] = self.getColor('colorWN6', self.playersInfo[dbID]['wn6'])

    def resetStats(self):
        self.dbIDs = []
        self.playersInfo = {}
        self._account_info = None
        self._account_tanks = None

    @staticmethod
    def getEFF(avgDmg, avgTier, avgFrags, avgSpot, avgCap, avgDef):
        return int(round(avgDmg * (10 / (avgTier + 2)) * (0.23 + 2 * avgTier / 100) + avgFrags * 250 + avgSpot * 150 + math.log(avgCap + 1, 1.732) * 150 + avgDef * 150))

    @staticmethod
    def getWN7(avgDmg, avgTier, avgFrags, avgSpot, avgDef, winrate, total):
        return int(round((1240 - 1040 / (min(avgTier, 6) ** 0.164)) * avgFrags + avgDmg * 530 / (184 * math.exp(0.24 * avgTier) + 130) + avgSpot * 125 * min(avgTier, 3) / 3 + min(avgDef, 2.2) * 100 + ((185 / (0.17 + math.exp(((winrate) - 35) * -0.134))) - 500) * 0.45 + (-1 * (((5 - min(avgTier, 5)) * 125) / (1 + math.exp((avgTier - (total / 220 ** (3 / avgTier))) * 1.5))))))

    @staticmethod
    def getWN6(avgDmg, avgTier, avgFrags, avgSpot, avgDef, winrate):
        return int(round((1240 - 1040 / (min(avgTier, 6)) ** 0.164) * avgFrags + avgDmg * 530 / (184 * math.exp(0.24 * avgTier) + 130) + avgSpot * 125 + min(avgDef, 2.2) * 100 + ((185 / (0.17 + math.exp((winrate - 35) * -0.134))) - 500) * 0.45 + (6 - min(avgTier, 6)) * -60))

    def loadVehiclesInfo(self):
        if self._vehiclesInfo is None:
            #startTime = time.time()
            url = 'https://raw.githubusercontent.com/VasyaPRO/StatsInBattle/master/vehicles_info.json'
            try:
                self._vehiclesInfo = json.loads(urllib2.urlopen(url).read())
                #print "vehicles info loaded [%s sec]" % str(time.time() - startTime)
            except IOError:
                showMessage('[StatsInBattle] Error loading vehicles.', "red")

    def getColor(self, rating, value):
        color = "FFFFFF"
        for i in range(len(config('colors/colorCodes'))):
            if value >= config('colors')[rating][i]:
                color = config('colors/colorCodes')[i]
        return color


class Analytics(object):
    def __init__(self):
        self._thread_analytics = None 
        self.trackingID = 'UA-78494860-1'
        self.appName = 'StatsInBattle'
        self.appVersion = __version__

    def getPlayerDBID(self):
        player = BigWorld.player()
        if hasattr(player,"databaseID"):
            return player.databaseID
        elif hasattr(player,"playerVehicleID"):
            return player.arena.vehicles[player.playerVehicleID]['accountDBID']
        else:
            #print "fail :D"
            time.sleep(5)
            return self.getPlayerDBID()

    def screenview(self):
        if config('allowAnalytics'):
            player = BigWorld.player()
            param = urllib.urlencode({
                'v': 1,
                't': 'screenview',
                'tid': '%s' % self.trackingID,
                'cid': '%s' % self.getPlayerDBID(),
                'an': '%s' % self.appName,
                'av': '%s' % self.appVersion,
                'cd': '%s [%s]' % (player.name, AUTH_REALM)
                })
            return urllib2.urlopen(url='http://www.google-analytics.com/collect?', data=param).read()

    def send_screenview(self):
        self._thread_analytics = threading.Thread(target=self.screenview)
        self._thread_analytics.start()

    def exception(self, description):
        if config('allowAnalytics'):
            player = BigWorld.player()
            param = urllib.urlencode({
                'v': 1,
                't': 'exception',
                'tid': '%s' % self.trackingID,
                'cid': '%s' % self.getPlayerDBID(),
                'an': '%s' % self.appName,
                'av': '%s' % self.appVersion,
                'cd': '%s [%s]' % (player.name, AUTH_REALM),
                'exd': '%s' % description
                })
            return urllib2.urlopen(url='http://www.google-analytics.com/collect?', data=param).read()

    def send_exception(self,description):
        self._thread_analytics = threading.Thread(target=self.exception, args=[description])
        self._thread_analytics.start()


def parse(string):
    try:
        return (re.match("<font color='#(.*?)'>(.*?)</font>", string).group(1), re.match("<font color='#(.*?)'>(.*?)</font>", string).group(2))
    except:
        return ('', '')


def showMessage(text, color='green'):
    if g_appLoader.getDefBattleApp() is not None:
        g_appLoader.getDefBattleApp().call('battle.PlayerMessagesPanel.ShowMessage', [0, text, color])
    elif isinstance(BigWorld.player(), PlayerAccount):
        SystemMessages.pushMessage(text, type = SystemMessages.SM_TYPE.Warning)
    else:
        print text

def handleKeyEvent(event):
    is_down, key, mods, is_repeat = game.convertKeyEvent(event)
    if key is getattr(Keys, config('reloadKey'), 0) and is_down:
        config.reload()
    #if key is getattr(Keys, "KEY_P") and is_down: # Debug
        #print stats.playersInfo

InputHandler.g_instance.onKeyDown += handleKeyEvent
InputHandler.g_instance.onKeyUp += handleKeyEvent


def new_Hangar__updateAll(self):
    old_Hangar__updateAll(self)
    #print "debug: Hangar.__updateAll"
    ga.send_screenview()

old_Hangar__updateAll = Hangar._Hangar__updateAll
Hangar._Hangar__updateAll = new_Hangar__updateAll


def new__onVehicleListUpdate(self, argStr):
    old__onVehicleListUpdate(self, argStr)
    #print "onVehicleListUpdate"
    stats.loadStats()
    
old__onVehicleListUpdate = ClientArena._ClientArena__onVehicleListUpdate
ClientArena._ClientArena__onVehicleListUpdate = new__onVehicleListUpdate


def new_Battle_beforeDelete(self):
    old_Battle_beforeDelete(self)
    stats.resetStats()

old_Battle_beforeDelete = Battle.beforeDelete
Battle.beforeDelete=new_Battle_beforeDelete


def new_BattleLoading_makeItem(self, vInfoVO, viStatsVO, userGetter, isSpeaking, actionGetter, regionGetter, playerTeam, isEnemy, squadIdx, isFallout = False):
    dbID = vInfoVO.player.accountDBID
    playerInfo = stats.playersInfo.get(str(dbID), None)
    if not config('battleLoading/enable') or playerInfo is None:
        return old_BattleLoading_makeItem(self, vInfoVO, viStatsVO, userGetter, isSpeaking, actionGetter, regionGetter, playerTeam, isEnemy, squadIdx, isFallout)
    makeItem = old_BattleLoading_makeItem(self, vInfoVO, viStatsVO, userGetter, isSpeaking, actionGetter, regionGetter, playerTeam, isEnemy, squadIdx, isFallout)
    makeItem['clanAbbrev'] = ''
    makeItem['vehicleGuiName']=(str(config('battleLoading/vehicle/left')) if vInfoVO.team == BigWorld.player().team else str(config('battleLoading/vehicle/right'))).format(**playerInfo)
    makeItem['playerName']=(str(config('battleLoading/nick/left')) if vInfoVO.team == BigWorld.player().team else str(config('battleLoading/nick/right'))).format(**playerInfo)
    return makeItem

old_BattleLoading_makeItem = BattleLoading._makeItem
BattleLoading._makeItem = new_BattleLoading_makeItem


def new_StatsForm_getFormattedStrings(self, vInfoVO, vStatsVO, viStatsVO, ctx, fullPlayerName):
    dbID = vInfoVO.player.accountDBID
    playerInfo = stats.playersInfo.get(str(dbID), None)
    if not config('playersPanel/enable') or playerInfo is None:
        return old_StatsFormget_FormattedStrings(self, vInfoVO, vStatsVO, viStatsVO, ctx, fullPlayerName)
    fullPlayerName, fragsString, vehicleName, strings, formatPanels = old_StatsFormget_FormattedStrings(self, vInfoVO, vStatsVO, viStatsVO, ctx, fullPlayerName)
    playerInfo['default_color'] = parse(vehicleName.replace('<br/>', ''))[0]
    if g_settingsCore.getSetting('ppState') == 'large':
        formatPanels = (str(config('playersPanel/large/nick/left')) if vInfoVO.team == BigWorld.player().team else str(config('playersPanel/large/nick/right'))).format(**playerInfo)
        vehicleName = (str(config('playersPanel/large/vehicle/left')) if vInfoVO.team == BigWorld.player().team else str(config('playersPanel/large/vehicle/right'))).format(**playerInfo)

    if g_settingsCore.getSetting('ppState') == 'medium2':
        vehicleName = (str(config('playersPanel/medium2/left')) if vInfoVO.team == BigWorld.player().team else str(config('playersPanel/medium2/right'))).format(**playerInfo)

    if g_settingsCore.getSetting('ppState') == 'medium':
        formatPanels = (str(config('playersPanel/medium/left')) if vInfoVO.team == BigWorld.player().team else str(config('playersPanel/medium/right'))).format(**playerInfo)
    return (fullPlayerName, fragsString, vehicleName, strings, formatPanels)

old_StatsFormget_FormattedStrings = _StatsForm.getFormattedStrings
_StatsForm.getFormattedStrings = new_StatsForm_getFormattedStrings


def new_BattleArenaController_makeHash(self,index, playerFullName, vInfoVO, vStatsVO, viStatsVO, ctx, playerAccountID, inviteSendingProhibited, invitesReceivingProhibited, isEnemy):
    dbID = vInfoVO.player.accountDBID
    playerInfo = stats.playersInfo.get(str(dbID), None)
    if not config('tab/enable') or playerInfo is None:
        return old_BattleArenaController_makeHash(self, index, playerFullName, vInfoVO, vStatsVO, viStatsVO, ctx, playerAccountID, inviteSendingProhibited, invitesReceivingProhibited, isEnemy)
    makeHash = old_BattleArenaController_makeHash(self, index, playerFullName, vInfoVO, vStatsVO, viStatsVO, ctx, playerAccountID, inviteSendingProhibited, invitesReceivingProhibited, isEnemy)
    makeHash['clanAbbrev'] = ''
    makeHash['vehicle']=(str(config('tab/vehicle/left')) if vInfoVO.team == BigWorld.player().team else str(config('tab/vehicle/right'))).format(**playerInfo)
    makeHash['userName']=(str(config('tab/nick/left')) if vInfoVO.team == BigWorld.player().team else str(config('tab/nick/right'))).format(**playerInfo)
    return makeHash

old_BattleArenaController_makeHash = BattleArenaController._makeHash
BattleArenaController._makeHash = new_BattleArenaController_makeHash


def new_MarkersManager_addVehicleMarker(self, vProxy, vInfo, guiProps):
    #print "add vehicle marker", vInfo.player.name
    dbID = vInfo.player.accountDBID
    playerInfo = stats.playersInfo.get(str(dbID), None)
    if not config('marker/enable') or playerInfo is None:
        return old_MarkersManager_addVehicleMarker(self, vProxy, vInfo, guiProps)

    vTypeDescr = vProxy.typeDescriptor
    maxHealth = vTypeDescr.maxHealth
    mProv = vProxy.model.node('HP_gui')
    isAlly = guiProps.isFriend
    speaking = False
    if GUI_SETTINGS.voiceChat:
        speaking = VoiceChatInterface.g_instance.isPlayerSpeaking(vInfo.player.accountDBID)
    hunting = VehicleActions.isHunting(vInfo.events)
    markerID = self._MarkersManager__ownUI.addMarker(mProv, 'VehicleMarkerAlly' if isAlly else 'VehicleMarkerEnemy')
    self._MarkersManager__markers[vInfo.vehicleID] = _VehicleMarker(markerID, vProxy, self._MarkersManager__ownUIProxy)
    battleCtx = g_sessionProvider.getCtx()
    result = battleCtx.getPlayerFullNameParts(vProxy.id)
    vType = vInfo.vehicleType
    squadIcon = ''
    if arena_info.isFalloutMultiTeam() and vInfo.isSquadMan():
        teamIdx = g_sessionProvider.getArenaDP().getMultiTeamsIndexes()[vInfo.team]
        squadIconTemplate = '%s%d'
        if guiProps.name() == 'squadman':
            squadTeam = 'my'
        elif isAlly:
            squadTeam = 'ally'
        else:
            squadTeam = 'enemy'
        squadIcon = squadIconTemplate % (squadTeam, teamIdx)
    self.invokeMarker(markerID, 'init', [vType.classTag,
     vType.iconPath,
     str(config('marker/vehicle')).format(**playerInfo), #result.vehicleName
     vType.level,
     result.playerFullName,
     str(config('marker/nick')).format(**playerInfo), #result.playerName
     "", #clanAbbrev
     result.regionCode,
     vProxy.health,
     maxHealth,
     guiProps.name(),
     speaking,
     hunting,
     guiProps.base,
     g_ctfManager.getVehicleCarriedFlagID(vInfo.vehicleID) is not None,
     squadIcon])
    return markerID

old_MarkersManager_addVehicleMarker = MarkersManager.addVehicleMarker
MarkersManager.addVehicleMarker = new_MarkersManager_addVehicleMarker


def new_BattleEntry_onAddToIgnored(self, _, uid, userName):
    old_BattleEntry_onAddToIgnored(self, _, uid, stats.playersInfo[str(int(uid))]['name'])

old_BattleEntry_onAddToIgnored = BattleEntry._BattleEntry__onAddToIgnored 
BattleEntry._BattleEntry__onAddToIgnored = new_BattleEntry_onAddToIgnored 


def new_BattleEntry_onAddToFriends(self, _, uid, userName):
    old_BattleEntry_onAddToFriends(self, _, uid, stats.playersInfo[str(int(uid))]['name'])

old_BattleEntry_onAddToFriends = BattleEntry._BattleEntry__onAddToFriends
BattleEntry._BattleEntry__onAddToFriends = new_BattleEntry_onAddToFriends 

ga = Analytics()
config = Config()
stats = Statistics()