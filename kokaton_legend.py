import math
import os
import random
import sys
import time
import pygame as pg


WIDTH, HEIGHT = 1600, 900  # ゲームウィンドウの幅，高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_bound(obj_rct:pg.Rect) -> tuple[bool, bool]:
    """
    Rectの画面内外判定用の関数
    引数：こうかとんRect，または，爆弾Rect，またはビームRect
    戻り値：横方向判定結果，縦方向判定結果（True：画面内／False：画面外）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:  # 横方向のはみ出し判定
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm

class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }
    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"  # こうかとんの無敵モードかの判定
        self.hyper_life = 0
        # HP表示の初期設定
        self.HP_limit = 5  # こうかとんの上限HP
        self.HP_life = 5  # こうかとんの初期HP
        self.damege = 1  # こうかとんの初期攻撃力
        self.font = pg.font.Font(None, 50)
        self.color = (255, 0, 0)
        self.HP_image = self.font.render(f"HP: {self.HP_life}/ {self.HP_limit}", 0, self.color)
        self.HP_rect = self.HP_image.get_rect()
        self.HP_rect.center = 400, HEIGHT - 50
        self.damege_image = self.font.render(f'Damage: {self.damege}', 0, self.color)
        self.damege_rect = self.HP_image.get_rect()
        self.damege_rect.center = 600, HEIGHT - 50

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
            if key_lst[pg.K_LSHIFT]: # 左Shiftキーが押されている場合、速度を倍にする
                self.speed = 10
            else:
                self.speed = 5
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.hyper_life > 0:
            self.state = "hyper"
            self.image = pg.transform.laplacian(self.image)
            self.hyper_life -= 1
        else:
            self.state = "normal"
        screen.blit(self.image, self.rect)
        self.HP_image = self.font.render(f"HP: {self.HP_life}/{self.HP_limit}", 0, self.color)  # HPの反映を表示させる
        screen.blit(self.HP_image, self.HP_rect)
        self.damege_image = self.font.render(f'Damage: {self.damege}', 0, self.color)  # 攻撃力を反映させる
        screen.blit(self.damege_image, self.damege_rect)

class Enemy_Beam(pg.sprite.Sprite):
     """
     敵のビーム（レーザー風）に関するクラス
     """
     colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

     def __init__(self, emy: "Enemy", bird:Bird):
         """
         ビームSurfaceを生成する
         引数1 emy:ビームを射出する敵機
         引数2 bird:攻撃対象のこうかとん
         """
         super().__init__()
         self.memoemx = emy.rect.centerx
         self.memoemy = emy.rect.centery
         self.kkx = bird.rect.centerx
         self.kky = bird.rect.centery
        
         #width, height = abs(self.kkx - self.memoemx) , 20
         self.image = pg.Surface((1600, 900))
        #  x_diff , y_diff = self.kkx-self.memoemx,self.kky-self.memoemy
        #  norm  = math.sqrt(x_diff**2+y_diff**2)
        #  vx,vy = x_diff/norm*math.sqrt(50),y_diff/norm*math.sqrt(50)
        #  angle = math.degrees(math.atan2(-vy, vx))
        #  self.image = pg.transform.rotozoom(self.image, angle,1.0)

         self.color = random.choice(__class__.colors)
         self.bold = 1
         
         pg.draw.line(self.image, self.color, (emy.rect.centerx,emy.rect.centery), (bird.rect.centerx,bird.rect.centery),self.bold)
         self.image.set_colorkey((0,0,0))
         self.rect = self.image.get_rect()

     def update(self,tmr):
          if tmr%10 == 0:
            self.bold += 1
          if self.bold < 10:
            pg.draw.line(self.image, self.color, (self.memoemx,self.memoemy), (self.kkx,self.kky),self.bold)
            return self.bold
          if self.bold == 11:
              self.kill()
                  

class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height/2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10
        self.damege = 1

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +6
        self.bound = random.randint(50, HEIGHT/2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル
        self.hp = 3

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy


class BIGsraim(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load("fig/suraim1.png")]
    
    def __init__(self):
        super().__init__()
        self.sraimx=random.randint(0, WIDTH)
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = self.sraimx, 0
        self.vy = +6
        self.bound = random.randint(50, HEIGHT/2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル
        self.hp = 2

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy


class SMALsraim1(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load("fig/suraim2.png")]
    
    def __init__(self,x,y):
        super().__init__()
        
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = x-50,y
        self.vy = +6
        self.bound = y  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル
        self.hp = 1

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy


class SMALsraim2(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load("fig/suraim2.png")]
    
    def __init__(self,x,y):
        super().__init__()
        
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = x+50,y
        self.vy = +6
        self.bound = y  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル    
        self.hp = 1

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy

class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class Enemysum:

    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 255, 255)
        self.value = 0
        self.image = self.font.render(f"enemy: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-100

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"enemy: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class nextround:

    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (255, 0, 255)
        self.value = 0
        self.image = self.font.render(f"next for : {5-self.value%5} Enemys", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 175, HEIGHT-150

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"next for : {5-self.value%5} Enemys", 0, self.color)
        screen.blit(self.image, self.rect)


class Gravity(pg.sprite.Sprite):
    def __init__(self, life:int):

        super().__init__()
        self.image = pg.Surface((1600, 900))
        self.rect = pg.draw.rect(self.image, 0, (0,0,WIDTH,HEIGHT))
        self.image.set_alpha(200) 
        self.life = life
    
    def update(self):

        self.life -=1
        if self.life< 0:
            self.kill()


class Shield(pg.sprite.Sprite):

    """
    防御壁に関するクラス
    """
    def __init__(self, bird: Bird, life: int):
        """
        防御壁を生成する
        Args:
            bird: こうかとんのインスタンス
            life: 防御壁の発動時間
        """
        super().__init__()
        width, height = bird.rect.height * 2,20
        self.image = pg.Surface((width, height))  # 手順1
        pg.draw.rect(self.image, (0, 0, 255), (0, 0, 20, bird.rect.height * 2))
        color = (0, 0, 255)
        self.life = life  # 防御壁の発動時間
        vx, vy = 1,1  # 手順3
        angle = math.degrees(math.atan2(-vy, vx))  # 手順4
        self.image = pg.transform.rotozoom(self.image, angle,1.0)
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx + vx * bird.rect.width  # 手順6
        self.rect.centery = bird.rect.centery + vy * bird.rect.height

    def update(self):
        """
        防御壁の発動時間を減算し、0未満になったら削除する
        """
        self.life -= 1
        if self.life < 0:
            self.kill()
 

class Round:
    def __init__(self): # ラウンド数表示
        self.round = 1
        self.font = pg.font.Font(None, 100)
        self.text = self.font.render(f"Round: {self.round}", 0, (255,255,255))
        self.rect = self.text.get_rect()
        self.rect.center = (800, 100)
        self.kill = 0
        self.flem = 200

    def update(self, screen: pg.surface):
        self.text = self.font.render(f"Round: {self.round}", 0, (255,255,255))
        screen.blit(self.text, self.rect)


class Bouns(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pg.image.load(f"fig/heart.png")
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +6
        self.bound = random.randint(50, HEIGHT/2)  # 停止位置

    def update(self):
        if self.rect.centery > self.bound:
            self.vy = 0
        self.rect.centery += self.vy


class Clear_Bou(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pg.image.load(f"fig/beam.png")
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +6
        self.bound = random.randint(50, HEIGHT/2)  # 停止位置

    def update(self):
        if self.rect.centery > self.bound:
            self.vy = 0
        self.rect.centery += self.vy


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()
    n=0
    sraimls=[]
    bird = Bird(3, (900, 400))
    e_beam = pg.sprite.Group()
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    gravity = pg.sprite.Group()
    shields = pg.sprite.Group()
    round = Round()
    hearts = pg.sprite.Group()
    attack_up = pg.sprite.Group()
    enemysum=Enemysum()
    nxt=nextround()
    tmr = 0
    clock = pg.time.Clock()

    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_g and score.value >= 200:  # キー「ｇ」が押される　かつ、　スコアが２００以上なら
                print(score.value)
                score.value -= 200
                gravity.add(Gravity(400))
            if event.type == pg.KEYDOWN and event.key == pg.K_k and score.value >= 100:  # 無敵状態の発動
                bird.hyper_life = 500
                score.value -= 100
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and score.value >= 50 and not shields: # シールド発動条件
                score.value -= 50 # スコア50消費
                shields.add(Shield(bird, 400)) # 400フレーム
        screen.blit(bg_img, [0, 0])

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            if round.round==1:
                emys.add(Enemy())
            else:
                sraim=BIGsraim()
                emys.add(sraim)
                sraimls.append(sraim)
            n+=1
            enemysum.value +=1
        if tmr%1500 == 0:  # 1000フレームに1回, HP回復できる
            hearts.add(Bouns())
        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))
                if round.round > 3:
                    e_beam.add(Enemy_Beam(emy,bird))

        for emy in pg.sprite.groupcollide(emys, beams, False , True).keys():
            for i in range(len(sraimls)):
                if emy==sraimls[i]:
                    emys.add(SMALsraim1(sraimls[i].sraimx,sraimls[i].bound))
                    emys.add(SMALsraim2(sraimls[i].sraimx,sraimls[i].bound))
                    exps.add(Explosion(emy, 10))  # 爆発エフェクト
                    score.value += 10  # 10点アップ
                    round.kill += 1
                    enemysum.value += 2
                    nxt.value+=1
                    bird.change_img(6, screen)  # こうかとん喜びエフェクト
            emy.take_damage(bird.damege)
            exps.add(Explosion(emy, 10))
            if emy.hp <= 0:
                exps.add(Explosion(emy, 100))  # 爆発エフェクト
                score.value += 10  # 10点アップ
                bird.change_img(6, screen)  # こうかとん喜びエフェクト
                round.kill+=1
                enemysum.value -= 1
                nxt.value+=1

        for emy in pg.sprite.groupcollide(emys, beams, False, True).keys():
            emy.take_damage(bird.damege)
            exps.add(Explosion(emy, 10))
            if emy.hp <= 0:
                exps.add(Explosion(emy, 100))  # 爆発エフェクト
                score.value += 10  # 10点アップ
                bird.change_img(6, screen)  # こうかとん喜びエフェクト
                round.kill+=1
                enemysum.value -= 1
                nxt.value+=1

        if bird.damege > 3:
            for bomb in pg.sprite.groupcollide(bombs, beams, True, False).keys():
                exps.add(Explosion(bomb, 30))  # 爆発エフェクト
                score.value += 1  # 1点アップ
        else:
            for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
                exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                score.value += 1  # 1点アップ

        for bomb in pg.sprite.groupcollide(bombs, gravity, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1

        for emy in pg.sprite.groupcollide(emys, gravity, True, False).keys():
            exps.add(Explosion(emy, 50))  # 爆発エフェクト
            score.value += 10
            round.kill += 1
            nxt.value+=1
            enemysum.value -= 1
            nxt.value+=1
            
        if len(pg.sprite.spritecollide(bird, hearts, True)) != 0:  # 空からのハートを拾うと回復できる
            if bird.HP_life < bird.HP_limit:
                bird.HP_life += 1
        if len(pg.sprite.spritecollide(bird, attack_up, True)) != 0:  # ビームを拾うと攻撃アップ
            bird.damege += 1
        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:  # こうかとんと爆弾の衝突判定
            if bird.state == "normal":
                bird.HP_life -= 1  # こうかとんが攻撃を耐えることができた
                if bird.HP_life <= 0:
                    bird.change_img(8, screen) # こうかとん悲しみエフェクト
                    score.update(screen)
                    pg.display.update()
                    time.sleep(2)
                    return
            else:
                score.value += 1

        # for beam in e_beam:
        #     print(beam.bold)
        #     if beam.bold >= 10:
        #        if pg.sprite.collide_rect(bird,beam):
        #             bird.change_img(8, screen) # こうかとん悲しみエフェクト
        #             score.update(screen)
        #             pg.display.update()
        #             time.sleep(2)
        #             return

        # 防御壁が存在し、爆弾が防御壁に衝突した場合は爆弾を削除する
        for bomb in pg.sprite.groupcollide(bombs, shields, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト

        if round.kill >= 5: # 5回キルをするとラウンド数が増える
            round.kill += 1
            round.round += 1
            round.kill = 0
            attack_up.add(Clear_Bou())  # ランドごとに攻撃力アップできる
            hearts.add(Bouns())
            if round.flem == 1:
                round.flem == 1
            if round.flem <= 50:
                round.flem -= 0.1
            else:
                 round.flem -= 50
        
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        hearts.update()
        hearts.draw(screen)  # ハートのブリット
        attack_up.update()
        attack_up.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        shields.update()
        shields.draw(screen)  # 防御壁の描画を追加
        score.update(screen)
        enemysum.update(screen)
        nxt.update(screen)
        gravity.update()
        gravity.draw(screen)
        e_beam.update(tmr)
        e_beam.draw(screen)
        bird.update(key_lst, screen)
        round.update(screen)
        pg.display.update()

        tmr += 1
        clock.tick(50)

        
if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()