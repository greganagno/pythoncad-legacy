#
# Copyright (c) 2010 Matteo Boscolo
#
# This file is part of PythonCAD.
#
# PythonCAD is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PythonCAD is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PythonCAD; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# This  module provide access to the undo part of the pythoncad database
#

from pycadbasedb            import PyCadBaseDb
from pycaddbexception       import UndoDb

class PyCadUndoDb(PyCadBaseDb):
    """
        this Class Provide all the basic operation to be made on the
        undo 
    """
    def __init__(self,dbConnection):
        PyCadBaseDb.__init__(self)
        if dbConnection is None:
            self.createConnection()
        else:
            self.setConnection(dbConnection)     
        _sqlCheck="""select * from sqlite_master where name like 'pycadundo'"""
        _table=self.makeSelect(_sqlCheck).fetchone()
        if _table is None:
            _sqlCreation="""CREATE TABLE "pycadundo" (
                                "pycad_id" INTEGER PRIMARY KEY,
                                "pycad_incremental_id" INTEGER
                                )
                                """
            self.makeUpdateInsert(_sqlCreation)
        _undoId=self.getLastUndoIndex()
        if _undoId is None:
            self.__lastUndo=0
        else:
            self.__lastUndo=_undoId
        self.__activeUndo=_undoId
        
    def getLastUndoIndex(self):
        """
            get the last undo index
        """
        _sqlCheck="select max(pycad_incremental_id) from pycadundo"
        _rows=self.makeSelect(_sqlCheck) 
        if _rows is None:            # no entity in the table
            _sqlInser="""INSERT INTO pycadundo (pycad_undo_state) VALUES ("active")"""
            self.makeUpdateInsert(_sqlInser)
            _rows=self.makeSelect(_sqlCheck) 
        if _rows is None:
            raise UndoDb, "No row fatched in undo search "
        _row=_rows.fetchone()
        return _row[0] # get the max index of the table 

    def dbUndo(self):
        """
            performe the undo operation 
        """
        _id=self.__activeUndo-1
        while _id>0:
            if self.undoIdExsist(_id):
                self.__activeUndo =_id
                break
            else:
                _id-=1
        if _id>0:
            _sqlInsert="""INSERT INTO pycadundo 
                        (pycad_incremental_id) VALUES (%s)"""%str(self.__activeUndo)
            self.makeUpdateInsert(_sqlInsert)
            return self.__activeUndo
        else:
            raise UndoDb,"The undo are finished Unable to perform the undo"
    
    def dbRedo(self):
        """
            perform the redo operation
        """
        _id=self.__activeUndo+1
        while _id<self.__lastUndo:
            if self.undoIdExsist(_id):
                self.__activeUndo =_id
                break
            else:
                _id+=1
        if _id<=self.__lastUndo:
            _sqlInsert="""INSERT INTO pycadundo 
                        (pycad_incremental_id) VALUES (%s)"""%str(_id)
            self.makeUpdateInsert(_sqlInsert)
            return _id
        else:
            raise UndoDb,"The undo are finished Unable to perform the redo"

    def undoIdExsist(self,undoId):
        """
            check is the undo id exsist
        """
        _sqlSelect="""SELECT pycad_incremental_id FROM pycadundo 
                      WHERE pycad_incremental_id =%s"""%str(undoId) 
        return not self.fetchOneRow(_sqlSelect) is None

    def getNewUndo(self):
        """
            get the next undo index pycadundo 
        """
        try:
            self.suspendCommit()        #suspend commit operation     
            self.__lastUndo+=1
            self.__activeUndo=self.__lastUndo
            _sqlInser="""INSERT INTO pycadundo 
                        (pycad_incremental_id) VALUES (%s)"""  %str(self.__lastUndo)
            self.makeUpdateInsert(_sqlInser)
            self.performCommit()
            return self.__lastUndo
        except:
            self.reactiveCommit()
            raise
        finally:
            self.reactiveCommit()
    
    def clearUndoTable(self):
        """
            Clear all the undo created 
        """
        _sqlDelete="""DELETE FROM pycadundo"""
        self.makeUpdateInsert(_sqlDelete)

    def deleteUndo(self,undoId):
        """
            delete the undo index
        """
        _sqlDelete="""DELETE FROM pycadundo WHERE 
                    (pycad_incremental_id) VALUES (%s)"""%str(undoId)
        self.makeUpdateInsert(_sqlDelete)  
 
    def getMaxUndoId(self):      
        """
            return the undo id
        """
        return self.__lastUndo
    def getActiveUndoId(self):
        """
            return the active undo id
        """
        return self.__activeUndo


def test():
    print "*"*10
    _undo=PyCadUndoDb(None)
    print "Clear db Table"
    _undo.clearUndoTable()
    print "create 10 undo "
    for i in range(10):
        _undo.getNewUndo()
    print "Undo"
    for i in range(11):
        _undo.dbUndo()
    print "redo"
    _undo.dbRedo()    