#################################################
# Term Project
#
# Name: Grant Yu
# Andrew Id: grantyu
# Recitation Section: I0
#################################################
#CITATION for a line using enumerate: https://stackoverflow.com/questions/6422700/how-to-get-indices-of-a-sorted-array-in-python
#CITATION for image import: https://stackoverflow.com/questions/43009527/how-to-insert-an-image-in-a-canvas-item

from cmu_112_graphics import *
import math
#import copy
import random

# AFFILIATIONS: player, enemy, neutral

class Button(object):
  
  def __init__(self,x1,y1,x2,y2,func,app,text='',font='Arial 12',color = 'white'):
    self.x1 = x1
    self.y1 = y1
    self.x2 = x2
    self.y2 = y2
    self.text = text
    self.color = color
    self.font = font
    self.func = func
    self.app = app
  
  def draw(self,canvas):
    x1 = self.x1
    x2 = self.x2
    y1 = self.y1
    y2 = self.y2
    canvas.create_rectangle(x1,y1,x2,y2,outline='black',fill=self.color)
    canvas.create_text((x1+x2)//2,(y1+y2)//2,text = self.text,font = self.font,fill='black')
  
  def isPressed(self,x,y):
    if x > self.x1 and x < self.x2 and y > self.y1 and y < self.y2:
      return True
    else:
      return False
  def activate(self):
    self.app.buttonlist.append(self)
  def deactivate(self):
    self.app.buttonlist.remove(self)
  def act(self):
    self.func(self)
    
  '''def ison(self,x,y):
    if x > x1 and x < x2 and y > y1 and y < y2:
      self.color = 'gray'
      return True
    else:
      self.color = 'white'
      return False'''

#################################################################33

class unit(object): #anything that has health, pretty much
  def __init__(self,x,y,affil,app,hp = 50,shd = 0,atk = 10,mana = 0,spd = 7,rng = 20,frq = 1):
    self.affil = affil #affiliation of unit
    self.x = x
    self.y = y
    self.hpmax = hp
    self.hp = hp
    self.shd = shd #shield
    self.atk = atk #attack
    self.mana = mana 
    self.spd = spd #speed
    self.rng = rng #range
    self.frq = frq #firing frequency per sec
    self.refreshCounter = 0 #changes to frq and decreases by 1 per frame
    self.selected = False #True if selected by mouse control
    self.atk_tgt = None #atk target (if exists)
    self.destination = None #location of the destination if specified 
    self.path = [] # list of (y,x) pairs, not (x,y)!!!
    self.dead = False
    self.canMove = True
    self.isAttacking = False
    self.refreshCounterMax = app.fps//self.frq
    self.app = app
    self.dir = (1,1)
    app.aliveList.append(self) #add newly created object to list of alive units

    if self.affil == "neutral":
      self.atklvl = 3
      self.shdlvl = 3
      self.hplvl = 3

    if self.affil == "player":
      self.atklvl = app.atklvl
      self.shdlvl = app.shdlvl
      self.hplvl = app.hplvl

    if self.affil == "enemy":
      self.atklvl = app.atklvle
      self.shdlvl = app.shdlvle
      self.hplvl = app.hplvle
    
    self.hp *= 1.2**self.hplvl
    self.atk *= 1.1**self.atklvl
    self.shd *= 1.1**self.shdlvl

    if isinstance(self,peasant):
      if self.affil == "player":
        self.lvl = app.pealvl-1
      if self.affil == "enemy":
        self.lvl = app.pealvle-1

    if isinstance(self,shooter):
      if self.affil == "player":
        self.lvl = app.shlvl-1
      if self.affil == "enemy":
        self.lvl = app.shlvle-1 

    if isinstance(self,tank):
      if self.affil == "player":
        self.lvl = app.tanklvl-1
      if self.affil == "enemy":
        self.lvl = app.tanklvle-1 

    if isinstance(self,airballoon):
      if self.affil == "player":
        self.lvl = app.ablvl-1
      if self.affil == "enemy":
        self.lvl = app.ablvle-1 
    
    if isinstance(self,aircraft):
      if self.affil == "player":
        self.lvl = app.aclvl-1
      if self.affil == "enemy":
        self.lvl = app.aclvle-1
    
    if isinstance(self,base):
      self.lvl = 0
    
    self.hp *= 1.1**self.lvl
    self.atk *= 1.1**self.lvl
    self.shd *= 1.1**self.lvl
    
    self.hpmax = self.hp
  
  def attack(self): #attack instructions for units
    if self.refreshCounter == 0:
      min_dist = 9000
      for enemy in self.app.aliveList: #find the closest enemy to hit, if any
        if enemy.affil != self.affil:
          d = dist(self,enemy)
          if isinstance(enemy,base):
            d = max(abs(self.x-enemy.x),abs(self.y-enemy.y))-enemy.basesz/2
            if (d <= self.rng) and (d <= min_dist):
              self.atk_tgt = enemy
          else:
            if (d <= self.rng) and (d <= min_dist):
              self.atk_tgt = enemy
        if self.atk_tgt != None: #attack happens, refresh counter set to frq
          self.canMove = False
          self.isAttacking = True
          a = self.atk
          dec = a**2/(math.exp(self.atk_tgt.shd-a)+a)
          self.atk_tgt.hp -= dec
          self.app.money += int(dec)          
          self.refreshCounter = self.refreshCounterMax
          #print(f'{self} attacked {self.atk_tgt}, causing {dec} damage!')
          if self.atk_tgt.hp <=0:
            self.atk_tgt = None
            self.canMove = True
    else:
      self.refreshCounter -= 1
      if self.refreshCounter == 2:
        self.isAttacking = False
  
  def setDestination(self,mouseX,mouseY,prt=False):
    if checkDest(mouseX,mouseY,self) == False:
      return None
    self.destination = (mouseX,mouseY)    
    self.path = pathFind(self.x,self.y,mouseX,mouseY,self)
    
  def move(self):
    if (self.path != []) and (self.canMove == True): #when doing certain tasks, e.g. fighting, unit cannot move
      for t in range(self.spd):
        if distg(self.x,self.y,self.path[0][0],self.path[0][1]) < 2**0.5*self.app.stepsize: #if reached block described by path
          # cut block and head to next pt
          del self.path[0]
        if self.path == []: #if destination reached, cut path
          self.destination = None
          break
        # else, calculate displacement and move one step forward
        dx = 2*(self.x > self.path[0][0])-1
        dy = 2*(self.y > self.path[0][1])-1
        if (abs(self.x-self.path[0][0]) < self.app.stepsize):
          dx = 0
        if (abs(self.y - self.path[0][1]) < self.app.stepsize):
          dy = 0
        self.x -= 2*dx
        self.y -= 2*dy
        if (dx,dy) != (0,0):
          self.dir = (dx,dy)
        else:
          self.dir = (1,1)

  def isDead(self): #checks if a unit is dead
    if self.hp <= 0:
      self.dead = True
      if self in self.app.aliveList:
        self.app.aliveList.remove(self)
      if isinstance(self,base):
        if self.affil == "player":
          self.app.playerbn -= 1
          if self.app.playerbn == 0:
            self.app.gstage = 'lose'
        if self.affil == "enemy":
          self.app.enemybn -= 1
          if self.app.enemybn == 0:
            self.app.gstage = 'win'
      return True
    else:
      return False

class peasant(unit):
  def __init__(self,x,y,affil,app):
    super().__init__(x,y,affil,app,hp = 50, shd = 0, atk = 10, mana = 0, spd = 5, rng = 25, frq = 2)

  def draw(self,canvas):
    if self.affil == 'player':
      if self.hp > 0:
        if self.selected == True:
          canvas.create_oval(self.x-5,self.y-5,self.x+5,self.y+5,fill='green',outline = 'cyan',width = 5)   
        if self.selected == False:
          if self.isAttacking == False:
            canvas.create_oval(self.x-5,self.y-5,self.x+5,self.y+5,fill='green')
          else:
            canvas.create_oval(self.x-5,self.y-5,self.x+5,self.y+5,fill='#30ff30')
            healthbardraw(self.x,self.y,10,self.hp,self.hpmax,canvas)
    if self.affil == 'enemy':
      if self.hp > 0:   
        if self.selected == False:
          if self.isAttacking == False:
            canvas.create_oval(self.x-5,self.y-5,self.x+5,self.y+5,fill='green',outline = 'red',width = 3)
          else:
            canvas.create_oval(self.x-5,self.y-5,self.x+5,self.y+5,fill='#30ff30',outline = 'red',width = 3)
            healthbardraw(self.x,self.y,10,self.hp,self.hpmax,canvas)

  def canPass(self,x1,y1,unit):
    if unit == self:
      return True
    if distg(x1,y1,self.x,self.y) <= 3:
      return False
    return True
  
  def isSelected(self,mouseX,mouseY): #checks if a unit is selected by mouse
    if distg(self.x,self.y,mouseX,mouseY) < 5:
      self.selected = True
    else:
      self.selected = False

class shooter(unit):
  def __init__(self,x,y,affil,app):
    super().__init__(x,y,affil,app,hp = 20, shd = 0, atk = 15, mana = 0, spd = 4, rng = 100, frq = 2)

  def draw(self,canvas):
    if self.hp > 0:
      if self.affil == 'player':
        if self.selected == True:
          canvas.create_oval(self.x-5,self.y-5,self.x+5,self.y+5,fill='green',outline = 'cyan',width = 5)   
        if self.selected == False:
          if self.isAttacking == False:
            canvas.create_oval(self.x-5,self.y-5,self.x+5,self.y+5,fill='green')
          else:
            canvas.create_oval(self.x-5,self.y-5,self.x+5,self.y+5,fill='#30ff30')
            healthbardraw(self.x,self.y,10,self.hp,self.hpmax,canvas)
      
      if self.affil == 'enemy':
        if self.isAttacking == False:
          canvas.create_oval(self.x-5,self.y-5,self.x+5,self.y+5,fill='green',outline='red',width=3)
        else:
          canvas.create_oval(self.x-5,self.y-5,self.x+5,self.y+5,fill='#30ff30',outline='red',width=3)
          healthbardraw(self.x,self.y,10,self.hp,self.hpmax,canvas)
      
      if self.atk_tgt != None:
        dg = distg(self.x,self.y,self.atk_tgt.x,self.atk_tgt.y)
        canvas.create_line(self.x, self.y, self.x+10*(self.atk_tgt.x-self.x)/dg, self.y+10*(self.atk_tgt.y-self.y)/dg,fill='red',width=3)
      else:
        canvas.create_line(self.x, self.y, self.x+7, self.y+7,width=3)
    

  def canPass(self,x1,y1,unit):
    if unit == self:
      return True
    if distg(x1,y1,self.x,self.y) <= 3:
      return False
    return True
  
  def isSelected(self,mouseX,mouseY): #checks if a unit is selected by mouse
    if distg(self.x,self.y,mouseX,mouseY) < 5:
      self.selected = True
    else:
      self.selected = False

class tank(unit):
  def __init__(self,x,y,affil,app):
    super().__init__(x,y,affil,app,hp = 500, shd = 70, atk = 100, mana = 0, spd = 3, rng = 125, frq = 4)

  def draw(self,canvas):
    if self.hp > 0:
      if self.affil == 'player':
        if self.selected == True:
          canvas.create_rectangle(self.x-10,self.y-10,self.x+10,self.y+10,fill='green',outline = 'cyan',width = 5)   
        if self.selected == False:
          canvas.create_rectangle(self.x-10,self.y-10,self.x+10,self.y+10,fill='green')
          if self.isAttacking == False:
            canvas.create_rectangle(self.x-5,self.y-5,self.x+5,self.y+5,fill = 'green')
          else:
            canvas.create_rectangle(self.x-5,self.y-5,self.x+5,self.y+5,fill='#30ff30')
            healthbardraw(self.x,self.y,10,self.hp,self.hpmax,canvas)
      if self.affil == 'enemy':
        canvas.create_rectangle(self.x-10,self.y-10,self.x+10,self.y+10,fill='green',outline='red',width=3)
        if self.isAttacking == False:
          canvas.create_rectangle(self.x-5,self.y-5,self.x+5,self.y+5,fill = 'green',outline='red',width=3)
        else:
          canvas.create_rectangle(self.x-5,self.y-5,self.x+5,self.y+5,fill='#30ff30',outline='red',width=3)
          healthbardraw(self.x,self.y,10,self.hp,self.hpmax,canvas)
      
      if self.atk_tgt != None:
        dg = distg(self.x,self.y,self.atk_tgt.x,self.atk_tgt.y)
        canvas.create_line(self.x, self.y, self.x+15*(self.atk_tgt.x-self.x)/dg, self.y+15*(self.atk_tgt.y-self.y)/dg,fill='red',width=4)
      else:
        canvas.create_line(self.x, self.y, self.x+15, self.y-15,width=4)

  def canPass(self,x1,y1,unit):
    if unit == self:
      return True
    if max(abs(x1-self.x),abs(y1-self.y)) <= 10:
      return False
    return True
  
  def isSelected(self,mouseX,mouseY): #checks if a unit is selected by mouse
    if distg(self.x,self.y,mouseX,mouseY) < 10:
      self.selected = True
    else:
      self.selected = False

class airballoon(unit):
  def __init__(self,x,y,affil,app):
    super().__init__(x,y,affil,app,hp = 100, shd = 0, atk = 30, mana = 0, spd = 5, rng = 35, frq = 2)

  def draw(self,canvas):
    if self.hp > 0:
      if self.affil == 'player':
        if self.selected == True:
          canvas.create_arc(self.x-10,self.y-10,self.x+10,self.y+10,start = 0, extent = 180, fill='green',outline = 'cyan',width=5)   
        if self.selected == False:
          if self.isAttacking == False:
            canvas.create_arc(self.x-10,self.y-10,self.x+10,self.y+10,start = 0, extent = 180, fill='green')
          else:
            canvas.create_arc(self.x-10,self.y-10,self.x+10,self.y+10,start = 0, extent = 180, fill='#30ff30')
            healthbardraw(self.x,self.y,10,self.hp,self.hpmax,canvas)
      if self.affil == "enemy":
        if self.isAttacking == False:
          canvas.create_arc(self.x-10,self.y-10,self.x+10,self.y+10,start = 0, extent = 180, fill='green',ouline='red',width=3)
        else:
          canvas.create_arc(self.x-10,self.y-10,self.x+10,self.y+10,start = 0, extent = 180, fill='#30ff30',ouline='red',width=3)
          healthbardraw(self.x,self.y,10,self.hp,self.hpmax,canvas)

  def canPass(self,x1,y1,unit):
    if unit == self:
      return True
    if distg(x1,y1,self.x,self.y) <= 3:
      return False
    return True
  
  def isSelected(self,mouseX,mouseY): #checks if a unit is selected by mouse
    if distg(self.x,self.y,mouseX,mouseY) < 10:
      self.selected = True
    else:
      self.selected = False

class aircraft(unit):
  def __init__(self,x,y,affil,app):
    super().__init__(x,y,affil,app,hp = 500, shd = 40, atk = 150, mana = 0, spd = 2, rng = 125, frq = 3)

  def draw(self,canvas):
    if self.hp > 0:
      if self.selected == True:
        canvas.create_polygon(self.x-5,self.y,self.x,self.y-10,self.x+5,self.y,self.x,self.y+10,fill='green',outline = 'cyan',width = 5)   
      if self.selected == False:
        if self.isAttacking == False:
          canvas.create_polygon(self.x-5,self.y,self.x,self.y-10,self.x+5,self.y,self.x,self.y+10,fill='green')
        else:
          canvas.create_polygon(self.x-5,self.y,self.x,self.y-10,self.x+5,self.y,self.x,self.y+10,fill='#30ff30')
          healthbardraw(self.x,self.y,10,self.hp,self.hpmax,canvas)

  def canPass(self,x1,y1,unit):
    if unit == self:
      return True
    if distg(x1,y1,self.x,self.y) <= 3:
      return False
    return True
  
  def isSelected(self,mouseX,mouseY): #checks if a unit is selected by mouse
    if distg(self.x,self.y,mouseX,mouseY) < 5:
      self.selected = True
    else:
      self.selected = False

class base(unit):
  def __init__(self,x,y,affil,app,basesz=0,hp = 2000, shd = 20, atk = 10, mana = 0, rng = 50, frq = 0.25):
    super().__init__(x,y,affil,app,hp,shd,atk,mana,0,rng,frq)
    if self.affil == 'player':
      self.app.playerbn += 1
    if self.affil == 'enemy':
      self.app.enemybn += 1
    self.storage = [] #stores list of units garrisoned
    if basesz == 0:
      self.basesz = app.basesz*2
    else:
      self.basesz = basesz
    self.rng += self.basesz/2
  
  def produce(self):
    app = self.app
    un = set()

    if self.affil == 'player':
      pealvl = app.pealvl
      shlvl = app.shlvl
      tanklvl = app.tanklvl
      ablvl = app.ablvl
      aclvl = app.aclvl
    if self.affil == 'enemy':
      pealvl = app.pealvle
      shlvl = app.shlvle
      tanklvl = app.tanklvle
      ablvl = app.ablvle
      aclvl = app.aclvle

    (dx,dy) = (random.randint(0,self.basesz)*0.9-self.basesz/2,random.randint(0,self.basesz)*0.9-self.basesz/2)
    if self.refreshCounter == 0:
      if (tanklvl == 0) and (ablvl == 0): #when no tank/balloon, produce peasants
        while checkDest(self.x+dx,self.y+dy,self) == False:
          (dx,dy) = (random.randint(0,self.basesz)*0.9-self.basesz/2,random.randint(0,self.basesz)*0.9-self.basesz/2)
        un.add(peasant(self.x+dx,self.y+dy,self.affil,self.app))
      
      if (shlvl > 0) and (tanklvl == 0) and (ablvl == 0): #when no tank/balloon & have shooters, produce shooters
        while checkDest(self.x+dx,self.y+dy,self) == False:
          (dx,dy) = (random.randint(0,self.basesz)*0.9-self.basesz/2,random.randint(0,self.basesz)*0.9-self.basesz/2)
        un.add(shooter(self.x+dx,self.y+dy,self.affil,self.app))
      
      if tanklvl > 0: #make tanks if possible, no more peasants/shooters
        self.frq = 0.1
        while checkDest(self.x+dx,self.y+dy,self) == False:
          (dx,dy) = (random.randint(0,self.basesz)*0.9-self.basesz/2,random.randint(0,self.basesz)*0.9-self.basesz/2)
        un.add(tank(self.x+dx,self.y+dy,self.affil,self.app))
      
      if ablvl > 0 and aclvl == 0: #make balloons if possible (but no aircrafts because they replace balloons), no more peasants/shooters
        while checkDest(self.x+dx,self.y+dy,self) == False:
          (dx,dy) = (random.randint(0,self.basesz)*0.9-self.basesz/2,random.randint(0,self.basesz)*0.9-self.basesz/2)
        un.add(airballoon(self.x+dx,self.y+dy,self.affil,self.app))

      if aclvl > 0: #make aircrafts, no more balloons
        self.frq = 0.1
        while checkDest(self.x+dx,self.y+dy,self) == False:
          (dx,dy) = (random.randint(0,self.basesz)*0.9-self.basesz/2,random.randint(0,self.basesz)*0.9-self.basesz/2)
        un.add(aircraft(self.x+dx,self.y+dy,self.affil,self.app))
      if self.affil == 'enemy':
        for u in un:
          u.setDestination(getX(0,app),getY(app.sz-1,app),True)

          
      
      self.refreshCounter = self.refreshCounterMax
    else:
      self.refreshCounter -= 1
    
  def isSelected(self,mouseX,mouseY): #checks if a base is selected by mouse
    if self.affil != 'player':
      return
    if max(abs(self.x+2+self.basesz/4-mouseX),abs(self.y-2-self.basesz/4-mouseY)) <= self.basesz/4 -2:
      self.selected = True
      self.app.gstage = 'upgrade'
      initUpgrades(self.app)
    else:
      self.selected = False

  def draw(self,canvas):
    if self.affil == 'neutral':
      color = self.app.colorList['nb']
    if self.affil == 'player':
      color = self.app.colorList['pb']
    if self.affil == 'enemy':
      color = self.app.colorList['eb']
    
    basesz = self.basesz
    if self.selected == False:
      canvas.create_rectangle(self.x-basesz/2,self.y-basesz/2,self.x+basesz/2,self.y+basesz/2,fill=color,outline='black',width=3)
    else:
      canvas.create_rectangle(self.x-basesz/2,self.y-basesz/2,self.x+basesz/2,self.y+basesz/2,fill=color,outline='yellow',width=3)
    canvas.create_text(self.x,self.y,text='BASE',font='Ariel 12 bold')
    healthbardraw(self.x,self.y-self.app.height/basesz/5,20,self.hp,self.hpmax,canvas)
    N = 0
    basePos = findCenter(self.x,self.y,self.app)
    for obj in self.app.aliveList:
      if obj.affil == self.affil and (isinstance(obj,base)== False):
        if findCenter(obj.x,obj.y,self.app) == basePos:
          N += 1
    canvas.create_text(self.x+self.app.height/basesz/3,self.y+self.app.height/basesz/3,text=str(N))

    if self.affil == 'player':
      canvas.create_rectangle(self.x+4,self.y-4,self.x+basesz/2,self.y-basesz/2,fill='yellow')
      dx = basesz//6
      dy = 2
      cx = self.x+2+basesz/4
      cy = self.y-2-basesz/4
      canvas.create_rectangle(cx-dx,cy-dy,cx+dx,cy+dy,fill='#a0a0ff',width=0)
      canvas.create_rectangle(cx-dy,cy-dx,cx+dy,cy+dx,fill='#a0a0ff',width=0)
  
    canvas.create_text(self.x-self.basesz/2,self.y-self.basesz/2,text=f'sh lvl: {self.shdlvl}')

  def canPass(self,x1,y1,unit):
    #if (unit.affil != self.affil) and (x1 >= self.x - self.basesz/2) and (x1 <= self.x + self.basesz/2) \
    #and (y1 >= self.y - self.basesz/2) and (y1 <= self.y + self.basesz/2):
      #return False
    return True

class obstacle(object):
  def __init__(self,x,y,app,basesz=0): #x,y in coordinates of bases
    self.x = x
    self.y = y
    self.app = app
    app.obstacles.append(self)
    if basesz == 0:
      self.basesz = app.basesz
    else:
      self.basesz = basesz

  def canPass(self,x1,y1,unit):
    if (x1 >= self.x - self.basesz/2) and (x1 <= self.x + self.basesz/2) \
    and (y1 >= self.y -self.basesz/2) and (y1 <= self.y + self.basesz/2):
      return False
    return True
  def draw(self,canvas):
    color = 'black'
    basesz = self.basesz
    canvas.create_rectangle(self.x-basesz/2,self.y-basesz/2,self.x+basesz/2,self.y+basesz/2,fill=color)
    
'''####################'''

#Button functions
def void(btn):
  return

def atkUp(btn):
  if btn.app.atklvl < 10 and btn.app.money > 100:
    btn.app.atklvl += 1
    btn.app.money -= 100
  if btn.app.atklvl == 10:
    btn.text = "ATK\nMAX"

def shdUp(btn):
  if btn.app.shdlvl < 10 and btn.app.money > 100:
    btn.app.shdlvl += 1
    btn.app.money -= 100
  if btn.app.shdlvl == 10:
    btn.text = "SHD\nMAX"

def hpUp(btn):
  if btn.app.hplvl < 10 and btn.app.money > 100:
    btn.app.hplvl += 1
    btn.app.money -= 100
  if btn.app.hplvl == 10:
    btn.text = "HP\nMAX"

def peaUp(btn):
  if btn.app.pealvl < 10 and btn.app.money > 100:
    btn.app.pealvl +=1
    btn.app.money -= 100
  if btn.app.pealvl == 10:
    btn.text = "PEASANT\nMAX"

def shUp(btn):
  if btn.app.shlvl < 10 and btn.app.money > 100:
    btn.app.shlvl +=1
    btn.app.money -= 100
  if btn.app.shlvl > 0:
    btn.text = "Shooter\nUpgrade"
  if btn.app.shlvl == 10:
    btn.text = "SHOOTER\nMAX"

def tankUp(btn):
  app = btn.app
  if app.shlvl >= 5 and app.pealvl >= 5:
    if btn.app.tanklvl < 10 and btn.app.money > 100:
      btn.app.tanklvl +=1
      btn.app.money -= 100
    if app.tanklvl > 0:
      btn.text = "Tank\nUpgrade"
    if app.tanklvl == 10:
      btn.text = "TANK\nMAX"
  else:
    btn.text = "need shooter\npeasant lvl 5"

def abUp(btn):
  app = btn.app  
  if app.shlvl >= 9:
    if btn.app.ablvl < 10 and btn.app.money > 100:
      btn.app.ablvl +=1
      btn.app.money -= 100
    if app.ablvl > 0:
      btn.text = "Air Balloon\nUpgrade"
    if app.ablvl == 10:
      btn.text = "AB\nMAX"
  else:
    btn.text = "need shooter\n lvl 9"

def acUp(btn):
  app = btn.app
  if app.ablvl >= 9:
    if btn.app.aclvl < 10 and btn.app.money > 100:
      btn.app.aclvl +=1
      btn.app.money -= 100
    if app.aclvl > 0:
      btn.text = "Aircraft\nUpgrade"
    if app.aclvl == 10:
      btn.text = "AC\nMAX"
  else:
    btn.text = "need balloon\n lvl 9"

def returnToGame(btn):
  btn.app.gstage = "game"

#app started

def appStarted(app):
  app.timerDelay = 50 # 50 ms, i.e. 20 fps
  app.fps = 1000//app.timerDelay 
  app.gstage = "start"
  app.startButton = Button(app.width//3,app.height//2,app.width*2//3,app.height*3//4,void,app,'Start','Arial 42 bold')  
  app.buttonlist = [app.startButton]
  app.margin = 0 #margin of battle map
  app.sz = 20 # of base-sized unit squares per side of battle map
  app.basesz = (app.width-2*app.margin)/app.sz
  app.aliveList = [] #stores units that are alive throughout the battle, only alive units will be active
  app.obstacles = []

  app.money = 0

  app.playerbn = 1
  app.enemybn = 1
  
  # initializes upgrades for player
  app.atklvl = 0
  app.shdlvl = 0
  app.hplvl = 0

  app.pealvl = 1
  app.shlvl = 0
  app.tanklvl = 0
  app.ablvl = 0
  app.aclvl = 0

  app.cost = 100
  #initalizes upgrades for enemy
  app.atklvle = 1
  app.shdlvle = 1
  app.hplvle = 1

  app.pealvle = 1
  app.shlvle = 1
  app.tanklvle = 0
  app.ablvle = 0
  app.aclvle = 0

  atkButton = Button(getX(4,app),getY(7,app),getX(6,app),getY(9,app),atkUp,app,'ATK\n+10%')
  shdButton = Button(getX(8,app),getY(7,app),getX(10,app),getY(9,app),shdUp,app,'SHD\n+10%')
  hpButton = Button(getX(12,app),getY(7,app),getX(14,app),getY(9,app),hpUp,app,'HP\n+20%')
  peaButton = Button(getX(4,app),getY(11,app),getX(6,app),getY(13,app),peaUp,app,'Upgrade\nPeasant')
  shButton = Button(getX(8,app),getY(11,app),getX(10,app),getY(13,app),shUp,app,'Unlock\nShooter')
  tankButton = Button(getX(12,app),getY(11,app),getX(14,app),getY(13,app),tankUp,app,'Unlock\nTank')
  abButton = Button(getX(6,app),getY(15,app),getX(8,app),getY(17,app),abUp,app,'Unlock\nBalloon')
  acButton = Button(getX(10,app),getY(15,app),getX(12,app),getY(17,app),acUp,app,'Unlock\nAircraft')
  returnButton = Button(getX(8,app),getY(18,app),getX(12,app),getY(19,app),returnToGame,app,'Return')
  app.upgradeButtons = [atkButton,shdButton,hpButton,peaButton,shButton,tankButton,abButton,acButton,returnButton]
  
  #app.dummylist = []
  app.stepsize = 15 #used for pathfinding of units
  #coloring scheme of battle map
  app.colorList = { #AFFILIATIONS: 'player','enemy','neutral'
    0: 'white',
    'p': 'black',
    'nb': 'gray',
    'pb': 'blue',
    'eb': 'red'
  }

############# Game components ##############
def mousePressed(app,event): #GAME STAGES (gstage): "start","game","upgrade","win","lose"
  if app.gstage == "start":
    if app.startButton.isPressed(event.x,event.y):
      app.gstage = "game"
      app.startButton.deactivate()
      initgame(app)
  
  if app.gstage == "game":
    for unit in app.aliveList:
      if unit.affil == 'player':
        if (unit.selected == True) and (not isinstance(unit,base)):
          unit.setDestination(event.x,event.y)
        unit.isSelected(event.x,event.y)

  if app.gstage == "upgrade":
    for b in app.buttonlist:
      if b.isPressed(event.x,event.y):
        b.act()
     
def drawStartScreen(app,canvas):
  app.startButton.draw(canvas)
  canvas.create_rectangle(app.width//6,10,app.width*5//6,70)
  canvas.create_text(app.width//2,40,text='Base rush',font='Arial 28 bold',fill='black')

def initgame(app): #initializes game
  '''playerbaseL = [((app.sz/2,app.height-app.sz/2))]
  enemybaseL = [(app.width-app.sz/2,app.sz/2)]
  neutralbaseL = [(app.sz/2,app.sz/2),(app.width/2,app.height/2),(app.width-app.sz/2,app.height-app.sz/2)]'''

  playerbaseL = [(0.5,app.sz-1.5)]
  enemybaseL = [(app.sz-1.5,0.5)]
  neutralbaseL = [(app.sz/2,app.sz/2),(app.sz-1.5,app.sz-1.5),(0.5,0.5)]
  obstacleL = []
  for j in range(app.sz-2):
    for k in range(app.sz-2):
      if (abs(j-k) > 1):
        obstacle(getX(j+1,app),getY(k+1,app),app)
  for k in playerbaseL:
    base(getX(k[0],app),getY(k[1],app),'player',app)
  for k in enemybaseL:
    base(getX(k[0],app),getY(k[1],app),'enemy',app)
  for k in neutralbaseL:
    base(getX(k[0],app),getY(k[1],app),'neutral',app)
  app.playerbn -= 1
  app.enemybn -= 1

################ Setting up upgrades page ################

def initUpgrades(app):
  for k in app.upgradeButtons:
    k.activate()
#################### Calculation Assistance #######################
def dist(unit1,unit2): #takes 2 units and returns their distances from each other
  return ((unit1.x-unit2.x)**2 + (unit1.y-unit2.y)**2)**0.5

def distg(x1,y1,x2,y2): #returns dist between (x1,y1,x2,y2)
  return ((x1-x2)**2 + (y1-y2)**2)**0.5

def getX(x,app): #convert grid coord onto actual coord
  gridWidth = app.width - 2*app.margin
  gridHeight = app.height - 2*app.margin
  #gridHeight = app.height - 2*app.margin-30
  cW = gridWidth/app.sz 
  cH = gridHeight/app.sz
  m = app.margin
  return m+(x+1/2)*cW    

def getY(y,app): 
  gridWidth = app.width - 2*app.margin
  gridHeight = app.height - 2*app.margin
  #gridHeight = app.height - 2*app.margin-30  
  cW = gridWidth/app.sz 
  cH = gridHeight/app.sz 
  m = app.margin
  #return m+(y+1/2)*cH+30 
  return m+(y+1/2)*cH

def findCenter(x,y,app):
  gridWidth = app.width - 2*app.margin
  gridHeight = app.height - 2*app.margin
  #gridHeight = app.height - 2*app.margin-30  
  cW = gridWidth/app.sz 
  cH = gridHeight/app.sz 
  m = app.margin
  return (round((x-m)/cW - 0.5),round((y-m)/cW - 0.5))

def checkDest(x,y,unit):
  app = unit.app
  if (0 > x) or (x > app.width) or (0 > y) or (y > app.height):
    return False
  for obs in app.aliveList:  
    if obs.canPass(x,y,unit) == False:
      return False
  for obs in app.obstacles:
    if obs.canPass(x,y,unit) == False:
      #print(f'obj at {(obs.x,obs.y)} blocks path')
      return False
  return True

'''
def pathFind(sx,sy,dx,dy,unit): #finds shortest path
  stpsize = unit.app.stepsize
  checklist = [(0,stpsize),(0,-stpsize),(stpsize,0),(-stpsize,0),
        (-stpsize,-stpsize),(-stpsize,stpsize),(stpsize,-stpsize),(+stpsize,+stpsize)]
  #checklist = [(0,stpsize),(0,-stpsize),(stpsize,0),(-stpsize,0)]  
  path = []
  prevchange = checklist[random.randint(0,7)]
  loc = (sx,sy)
  cnt = 0
  repeatcnt = 0
  inccnt = 0
  while cnt < 2000:
    cnt += 1
    if (checkDest(loc[0]+prevchange[0],loc[1]+prevchange[1],unit) == False):
      prevchange = checklist[random.randint(0,7)]
    else:
      olddist = distg(loc[0],loc[1],dx,dy)
      loc = (int(loc[0]+prevchange[0]),int(loc[1]+prevchange[1]))
      inccnt += (distg(loc[0],loc[1],dx,dy) > olddist)

      if (loc not in path) and (inccnt < 2):
        path.append(loc)
        if distg(loc[0],loc[1],dx,dy) < stpsize:
          return path
      else:
        if inccnt == 2:
          inccnt = 0
        repeatcnt += 1
        prevchange = checklist[random.randint(0,7)]
        if repeatcnt == 20:
          repeatcnt = 0
          if len(path) > 1:
            loc = path[-2]
            del path[-1]

  return [] 
'''

def pathFind(sx,sy,dx,dy,unit): #finds shortest path
  stpsize = unit.app.stepsize
  checklist = [(0,stpsize),(0,-stpsize),(stpsize,0),(-stpsize,0),
        (-stpsize,-stpsize),(-stpsize,stpsize),(stpsize,-stpsize),(+stpsize,+stpsize)]
  #checklist = [(0,stpsize),(0,-stpsize),(stpsize,0),(-stpsize,0)]  
  path = []
  prevchange = None
  loc = (sx,sy)
  cnt = 0
  while cnt < 100:
    cnt += 1
    distlist = [distg(loc[0]+u[0],loc[1]+u[1],dx,dy) for u in checklist] 
    
    sI = [i[0] for i in sorted(enumerate(distlist), key=lambda x:x[1])] #list of indices when distlist sorted in increasing order 
    '''CITATION for line immediately above: https://stackoverflow.com/questions/6422700/how-to-get-indices-of-a-sorted-array-in-python'''

    for k in range(len(sI)):
      prevchange = checklist[sI[k]]
      if (checkDest(loc[0]+prevchange[0],loc[1]+prevchange[1],unit) == True) and (distlist[sI[k]] < distg(loc[0],loc[1],dx,dy)):
        loc = (int(loc[0]+prevchange[0]),int(loc[1]+prevchange[1]))
        path.append(loc)
        if distg(loc[0],loc[1],dx,dy) < stpsize:
          return path
        break
      if (k == len(sI)-1):
        return path

'''def pathFind(sx,sy,dx,dy,unit): #finds shortest path on some graph embedded in grid, from starting point (sx,sy) to destination (dx,dy)
  currentlevel = set()
  currentlevel.add((sx,sy))
  nextlevel = set()
  visited = set()
  visited.add((sx,sy))
  parents = dict()
  stop = 0
  stop1 = 0
  stpsize = unit.app.stepsize
  while stop == 0: #traversing down the tree
    for u in currentlevel:
      checkset = {(u[0],u[1]+stpsize),(u[0],u[1]-stpsize),(u[0]+stpsize,u[1]),(u[0]-stpsize,u[1]),\
        (u[0]-stpsize,u[1]-stpsize),(u[0]-stpsize,u[1]+stpsize),(u[0]+stpsize,u[1]-stpsize),(u[0]+stpsize,u[1]+stpsize)}
      for c in checkset:
        if (c not in visited) and (checkDest(c[0],c[1],unit) == True):
          visited.add(c)
          parents[c] = u
          nextlevel.add(c)
          if distg(c[0],c[1],dx,dy) < stpsize:
            stop = 1
            stop1 = 1
            (dx1,dy1) = (c[0],c[1])
            break
      if stop1 == 1:
        break
    if len(nextlevel) == 0:
      return set()
    currentlevel = copy.copy(nextlevel)
    nextlevel = set()
  
  cntr = (dx1,dy1) #backtrack to parent node for path
  while cntr != (sx,sy):  
    cntrHist.append(cntr)
    cntr = parents[cntr]
  cntrHist.reverse()
  return cntrHist #list of (y,x) pairs'''


###################### Drawing Functions ######################################

def healthbardraw(x,y,length,hp,maxhp,canvas):
  canvas.create_rectangle(x-length,y-15,x+length,y-12)
  canvas.create_rectangle(x-length,y-15,x-length+2*length*hp//maxhp,y-12,fill='red')

def drawMap(app,canvas):
	for k in app.obstacles:
		k.draw(canvas)
      
def timerFired(app):
  if app.gstage == 'game':
    for obj in app.aliveList: 
      obj.attack()
    for obj in app.aliveList:
      obj.isDead()
    for obj in app.aliveList: 
      if isinstance(obj,base) and obj.affil != 'neutral':
        obj.produce()
      else:
        obj.move()

def drawGame(app,canvas):
  drawMap(app,canvas)
  for obj in app.aliveList:
    obj.draw(canvas)

def drawUpgrades(app,canvas):
  canvas.create_text(app.width//6,app.height//10,text=f'Money: {app.money}',font='Arial 18 bold')
  canvas.create_rectangle(app.width//3,app.height//20,app.width*2//3,app.height*3//20)
  canvas.create_text(app.width/2,app.height//10,text='Upgrades',font='Arial 24 bold')
  canvas.create_text(app.width/2,app.height//5,text='Each upgrade costs $100, earn more money by causing damage!',font = 'Arial 12 bold')
  for b in app.buttonlist:
    b.draw(canvas)
  canvas.create_text(app.width*6//7,app.height*4//7,text=f"Multipliers: \n ATK: {1.1**app.atklvl}\n SHD: {1.1**app.shdlvl} \n HP: {1.2**app.hplvl} \n peasant: {1.1**app.pealvl} \n shooter: {1.1**app.shlvl} \n tank: {1.1**app.tanklvl} \n airballoon: {1.1**app.ablvl} \n aircraft: {1.1**app.aclvl} ")

def drawLosingScreen(app,canvas):
  canvas.create_text(app.width//2,app.height//2,text='You Lost',font='Arial 28 bold',fill='red')

def drawWinningScreen(app,canvas):
  canvas.create_text(app.width//2,app.height//2,text='You Win!',font='Arial 28 bold',fill='blue')

def redrawAll(app, canvas):
  if app.gstage == 'start':
    drawStartScreen(app,canvas)
  if app.gstage == 'game':
    drawGame(app,canvas)
  if app.gstage == 'upgrade':
    drawUpgrades(app,canvas)
  '''for c in app.dummylist:
    canvas.create_oval(c[0]-2,c[1]-2,c[0]+2,c[1]+2,fill='red')'''
  if app.gstage == 'lose':
    drawLosingScreen(app,canvas)
  if app.gstage == 'win':
    drawWinningScreen(app,canvas)

runApp(width=600, height=600)