class Proxy:
    def __init__( self, subject ):
        self.__subject = subject
    def __getattr__( self, name ):
        return getattr( self.__subject, name )

class RGB:
    def __init__( self, red, green, blue ):
        self.__red = red
        self.__green = green
        self.__blue = blue
    def Red( self ):
        return self.__red
    def Green( self ):
        return self.__green
    def Blue( self ):
        return self.__blue

class NoBlueProxy( Proxy ):
    def Blue( self ):
        return 0
    def yap(self):
        return "haha"