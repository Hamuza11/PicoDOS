from sys import platform,ps1
from os import getcwd,listdir,chdir,mkdir,rmdir
try:
    from fbconsole import FBConsole
    from PicoGameBoy import ST7789
    from os import dupterm
    p=ST7789()
    s=FBConsole(p)
    dupterm(s)
    del p
except:
    pass
user="root"
def prmt():
    cmd=input(user+"@"+platform+":"+getcwd()+" # ")
    arg=cmd.split(" ")
    return arg

osfiles={"dos.py","fbconsole.py","PicoGameBoy.py"}
while True:
    arg=prmt()
    if arg[0]=="cwd":
        print(getcwd())
        continue
    elif arg[0]=="dir":
        try:
            folder=arg[1]
        except IndexError:
            folder=getcwd()
        finally:
            f=listdir(folder)
            for file in f:
                print(file)
        continue
    elif arg[0]=="cd":
        try:
            path=arg[1]
        except IndexError:
            path="/"
        finally:
            chdir(path)
            continue
    elif arg[0]=="md":
        try:
            mkdir(arg[1])
            continue 
        except IndexError:
            print("MD needs a path")
            continue
    elif arg[0]=="rd":
        try:
            rmdir(arg[1])
            continue 
        except IndexError:
            print("RD needs a path")
            continue 
    elif arg[0]=="python":
        try:
            exec(f"exec(open('{arg[1]}').read())")
        except:    
            sh=input(ps1)
            if sh=="leave":
                continue
            try:
                while True:
                    c=exec(sh)
                    del c
                    sh=input(ps1)
                    continue
            except Exception as ex:
                print(ex)
    elif arg[0]=="edit":
        if arg[1] in osfiles:
            print("This is a system file.")
            continue 
        try:
            f=open(arg[1],"a")
        except IndexError:
            print("EDIT needs a path")
            continue
        try:    
            while True :    
                txt=input()
                f.write(txt+"\n")
        except KeyboardInterrupt:
            f.flush()
            del f
            continue
    elif arg[0]=="cls":
        s.cls()
        continue
    elif arg[0]=="username":
        try:
            user=arg[1]
        except IndexError:
            print(user)
        finally:
            continue 
    elif arg[0]=="":
        continue 
    else:
        print("unknown command: "+arg[0])
        continue
        
            
