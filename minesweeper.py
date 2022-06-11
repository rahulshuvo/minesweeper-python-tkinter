
import ast
import tkinter as ttk
from tkinter import messagebox as tkMessageBox
from collections import deque
import random
import platform
from datetime import datetime
import sys
import os


STATE_DEFAULT = 0
STATE_CLICKED = 1
STATE_FLAGGED = 2

BTN_CLICK = "<Button-1>"
BTN_FLAG = "<Button-2>" if platform.system() == 'Darwin' else "<Button-3>"

window = None

class Minesweeper:

    def __init__(self, tk):

        # import images
        self.images = {
            "plain": ttk.PhotoImage(file = "images/tile_plain.gif"),
            "clicked": ttk.PhotoImage(file = "images/tile_clicked.gif"),
            "mine": ttk.PhotoImage(file = "images/tile_mine.gif"),
            "flag": ttk.PhotoImage(file = "images/tile_flag.gif"),
            "wrong": ttk.PhotoImage(file = "images/tile_wrong.gif"),
            "numbers": []
        }
        for i in range(1, 9):
            self.images["numbers"].append(ttk.PhotoImage(file = "images/tile_"+str(i)+".gif"))

        # set up frame
        self.tk = tk
        self.frame = ttk.Frame(self.tk)
        self.frame.pack()

        # set up labels/UI
        self.labels = {
            "time": ttk.Label(self.frame, text = "00:00:00"),
            "mines": ttk.Label(self.frame, text = "Mines: 0"),
            "flags": ttk.Label(self.frame, text = "Flags: 0"),
            "clear grids": ttk.Label(self.frame, text = "clear grids: 0"),
        }

        self.restart() # start game
    
    def restart_program(self):
        os.execl(sys.executable, '"{}"'.format(sys.executable), *sys.argv)

    def restart(self):
        self.getInput()

    def getInput(self):
        global x,x_label,y,y_label,mine,mine_label,start_button, load_button  # use global variables for futher usage etc remove if not needed

        x_label = ttk.Label(self.frame, text = "enter column size")
        x_label.pack()

        x = ttk.Entry(self.frame) # create entry field for number of columns
        x.pack(pady=5,padx=15) 

        y_label = ttk.Label(self.frame, text = "enter row size")
        y_label.pack()

        y = ttk.Entry(self.frame) # create entry field for number of rows
        y.pack(pady=5,padx=15)
        
        mine_label = ttk.Label(self.frame, text = "enter max mine count")
        mine_label.pack()

        mine = ttk.Entry(self.frame) # create entry field for number of mines
        mine.pack(pady=5,padx=15)

        start_button = ttk.Button(
        self.frame,
        text="start",
        command= self.startGame
        ) # create start button
        start_button.pack(pady=10) 

        load_button = ttk.Button(
        self.frame,
        text="load Save game",
        command= self.loadGame
        ) # create button for loading saved game
        load_button.pack(pady=10)
        
        
    def startGame(self):
        #get input value
        self.SIZE_X = int(x.get())
        self.SIZE_Y = int(y.get())
        self.MAX_MINE_COUNT = int(mine.get())

        self.removeInputView()
        self.setup()
        self.refreshLabels()
        self.updateTimer() # init timer

    def setupLabels(self):
        self.labels["time"].grid(row=0, column=0, columnspan=self.SIZE_Y) # time label
        self.labels["mines"].grid(row=self.SIZE_X+1, column=0, columnspan=self.SIZE_Y) # mines label
        self.labels["flags"].grid(row=self.SIZE_X+2, column=0, columnspan=self.SIZE_Y) # flags label
        self.labels["clear grids"].grid(row=self.SIZE_X+3, column=0, columnspan=self.SIZE_Y) # clear grids label

    def setup(self):
        # create flag and clicked tile variables
        self.flagCount = 0
        self.correctFlagCount = 0
        self.clickedCount = 0
        self.startTime = None

        self.setupLabels()
        self.setupButton()

        # create buttons
        self.tiles = dict({}) # create dictionary for tiles
        self.mines = 0
        for x in range(0, self.SIZE_X):
            for y in range(0, self.SIZE_Y):
                if y == 0:
                    self.tiles[x] = {}

                id = str(x) + "_" + str(y)
                isMine = False

                # default tile image
                gfx = self.images["plain"]

                # currently less or equal amount of max mines
                if random.uniform(0.0, 1.0) < 0.1 and self.mines < self.MAX_MINE_COUNT:
                    isMine = True
                    self.mines += 1

                tile = {
                    "id": id,
                    "isMine": isMine,
                    "state": STATE_DEFAULT,
                    "coords": {
                        "x": x,
                        "y": y
                    },
                    "button": ttk.Button(self.frame, image = gfx),
                    "mines": 0 # calculated after grid is built
                }

                tile["button"].bind(BTN_CLICK, self.onClickWrapper(x, y))
                tile["button"].bind(BTN_FLAG, self.onRightClickWrapper(x, y))
                tile["button"].grid( row = x+1, column = y ) # offset by 1 row for timer

                self.tiles[x][y] = tile

        # loop again to find nearby mines and display number on tile
        for x in range(0, self.SIZE_X):
            for y in range(0, self.SIZE_Y):
                mc = 0
                for n in self.getNeighbors(x, y):
                    mc += 1 if n["isMine"] else 0
                self.tiles[x][y]["mines"] = mc

    def removeInputView(self):
        # remove input view
        x.destroy()
        x_label.destroy()
        y.destroy()
        y_label.destroy()
        mine.destroy()
        mine_label.destroy()
        start_button.destroy()
        load_button.destroy()

    
    def startSaveGame(self):
        self.removeInputView()
        self.setupSave()
        self.refreshLabels()
        self.updateTimer() # init timer
    
    def setupButton(self):
        ttk.Button(
        self.frame,
        text="Restart",
        command= self.restart_program
        ).grid(row = self.SIZE_X+4, column = 0, columnspan = self.SIZE_Y) # restart button

        ttk.Button(
        self.frame,
        text="save Data and Quit",
        command= self.saveData
        ).grid(row = self.SIZE_X+6, column = 0, columnspan = self.SIZE_Y) # save game button

        ttk.Button(
        self.frame,
        text="computer Play",
        command= self.aiPlay
        ).grid(row = self.SIZE_X+8, column = 0, columnspan = self.SIZE_Y) # computer play button

    def setupSave(self):
        # create flag and clicked tile variables
        self.correctFlagCount = 0
        self.startTime = None

        self.setupLabels()
        self.setupButton()

        # create buttons
        for x in range(0, self.SIZE_X):
            for y in range(0, self.SIZE_Y):
                gfx = self.images["plain"]
                
                tile = {
                    "id": self.tiles[x][y]['id'],
                    "isMine": self.tiles[x][y]['isMine'],
                    "state": self.tiles[x][y]['state'],
                    "coords": self.tiles[x][y]['coords'],
                    "button": ttk.Button(self.frame, image = gfx),
                    "mines": self.tiles[x][y]['mines']
                }
                tile["button"].bind(BTN_CLICK, self.onClickWrapper(x, y))
                tile["button"].bind(BTN_FLAG, self.onRightClickWrapper(x, y))
                tile["button"].grid( row = x+1, column = y )

                if(tile["state"] == STATE_FLAGGED):
                    tile["button"].config(image = self.images["flag"])
                    tile["button"].unbind(BTN_CLICK)

                if(tile["state"] == STATE_CLICKED):
                    if tile["mines"] == 0:
                        tile["button"].config(image = self.images["clicked"])
                        self.clearSurroundingTiles(tile["id"])
                    else:
                        tile["button"].config(image = self.images["numbers"][tile["mines"]-1])

                self.tiles[x][y] = tile

    
    def saveData(self):
        saveTiles = self.tiles
        for key in saveTiles:
            for key2 in saveTiles[key]:
                saveTiles[key][key2].pop("button")
        with open('output.txt', 'w') as f:
            f.write(str(saveTiles))
        self.tk.destroy() # close window after saving data

    def loadGame(self):
        with open('output.txt') as f:
            grid = f.readline()
        self.tiles = ast.literal_eval(grid)
        self.SIZE_X = len(self.tiles) # get x size of grid
        self.mines = 0
        self.flagCount = 0
        self.clickedCount = 0
        for key in self.tiles:
            self.SIZE_Y = len(self.tiles[key]) # get y size of grid
            for key2 in self.tiles[key]:
                self.mines += self.tiles[key][key2]["isMine"] # get amount of mines
                self.flagCount += self.tiles[key][key2]["state"] == STATE_FLAGGED # get amount of flags
                self.clickedCount += self.tiles[key][key2]["state"] == STATE_CLICKED # get amount of clicked tiles
                
        self.startSaveGame()


    def aiPlay(self):
        x= random.randrange(0, self.SIZE_X) # random x
        y= random.randrange(0, self.SIZE_Y) # random y
        click = random.randrange(0, 2) # random click
        if(click == 0):
            self.onClick(self.tiles[x][y])
        else:
            self.onRightClick(self.tiles[x][y])

        self.frame.after(1000, self.aiPlay) # call again after 1 second
        

    def refreshLabels(self):
        self.labels["flags"].config(text = "Flags: "+str(self.flagCount))
        self.labels["mines"].config(text = "Mines: "+str(self.mines))
        self.labels["clear grids"].config(text = "clear grids: "+str(self.clickedCount))

    def gameOver(self, won):
        for x in range(0, self.SIZE_X):
            for y in range(0, self.SIZE_Y):
                if self.tiles[x][y]["isMine"] == False and self.tiles[x][y]["state"] == STATE_FLAGGED:
                    self.tiles[x][y]["button"].config(image = self.images["wrong"]) 
                if self.tiles[x][y]["isMine"] == True and self.tiles[x][y]["state"] != STATE_FLAGGED:
                    self.tiles[x][y]["button"].config(image = self.images["mine"]) 

        self.tk.update()

        msg = "You Win! Play again?" if won else "You Lose! Play again?"
        res = tkMessageBox.askyesno("Nice!" if won else "Game Over", msg)
        if res:
            self.restart_program()
        else:
            self.tk.destroy()

    def updateTimer(self):
        ts = "00:00:00"
        if self.startTime != None:
            delta = datetime.now() - self.startTime
            ts = str(delta).split('.')[0] # drop ms
            if delta.total_seconds() < 36000:
                ts = "0" + ts # zero-pad
        self.labels["time"].config(text = ts)
        self.frame.after(100, self.updateTimer)

    def getNeighbors(self, x, y):
        neighbors = []
        coords = [
            {"x": x-1,  "y": y-1},  #top right
            {"x": x-1,  "y": y},    #top middle
            {"x": x-1,  "y": y+1},  #top left
            {"x": x,    "y": y-1},  #left
            {"x": x,    "y": y+1},  #right
            {"x": x+1,  "y": y-1},  #bottom right
            {"x": x+1,  "y": y},    #bottom middle
            {"x": x+1,  "y": y+1},  #bottom left
        ]
        for n in coords:
            try:
                neighbors.append(self.tiles[n["x"]][n["y"]])
            except KeyError:
                pass
        return neighbors

    def onClickWrapper(self, x, y):
        return lambda Button: self.onClick(self.tiles[x][y])

    def onRightClickWrapper(self, x, y):
        return lambda Button: self.onRightClick(self.tiles[x][y])

    def onClick(self, tile):
        if self.startTime == None:
            self.startTime = datetime.now()

        if tile["isMine"] == True:
            # end game
            self.gameOver(False)
            return

        # change image
        if tile["mines"] == 0:
            tile["button"].config(image = self.images["clicked"])
            self.clearSurroundingTiles(tile["id"])
        else:
            tile["button"].config(image = self.images["numbers"][tile["mines"]-1])
        # if not already set as clicked, change state and count
        if tile["state"] != STATE_CLICKED:
            tile["state"] = STATE_CLICKED
            self.clickedCount += 1
        if self.clickedCount == (self.SIZE_X * self.SIZE_Y) - self.mines:
            self.gameOver(True)
        self.refreshLabels()

    def onRightClick(self, tile):
        if self.startTime == None:
            self.startTime = datetime.now()

        # if not clicked
        if tile["state"] == STATE_DEFAULT:
            tile["button"].config(image = self.images["flag"])
            tile["state"] = STATE_FLAGGED
            tile["button"].unbind(BTN_CLICK)
            # if a mine
            if tile["isMine"] == True:
                self.correctFlagCount += 1
            self.flagCount += 1
            self.refreshLabels()
        # if flagged, unFlag
        elif tile["state"] == 2:
            tile["button"].config(image = self.images["plain"])
            tile["state"] = 0
            tile["button"].bind(BTN_CLICK, self.onClickWrapper(tile["coords"]["x"], tile["coords"]["y"]))
            # if a mine
            if tile["isMine"] == True:
                self.correctFlagCount -= 1
            self.flagCount -= 1
            self.refreshLabels()

    def clearSurroundingTiles(self, id):
        queue = deque([id])

        while len(queue) != 0:
            key = queue.popleft()
            parts = key.split("_")
            x = int(parts[0])
            y = int(parts[1])

            for tile in self.getNeighbors(x, y):
                self.clearTile(tile, queue)

    def clearTile(self, tile, queue):
        if tile["state"] != STATE_DEFAULT:
            return

        if tile["mines"] == 0:
            tile["button"].config(image = self.images["clicked"])
            queue.append(tile["id"])
        else:
            tile["button"].config(image = self.images["numbers"][tile["mines"]-1])

        tile["state"] = STATE_CLICKED
        self.clickedCount += 1

### END OF CLASSES ###

def main():
    # create Tk instance
    window = ttk.Tk()
    # set program title
    window.title("Minesweeper")
    # set window icon
    window.iconphoto(False, ttk.PhotoImage(file = "images/tile_mine.gif"))
    Minesweeper(window)
    # run event loop
    window.mainloop()

if __name__ == "__main__":
    main()
