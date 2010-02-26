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
# This module provide basic operation for the entity in the pythoncad database
#

import cPickle

from pycadent               import PyCadEnt
from Entity.pycadstyle      import PyCadStyle
from pycadbasedb            import PyCadBaseDb

class PyCadEntDb(PyCadBaseDb):
    """
        this class provide the besic operation for the entity
    """
    def __init__(self,dbConnection):
        PyCadBaseDb.__init__(self)
        if dbConnection is None:
            self.createConnection()
        else:
            self.setConnection(dbConnection)

        _sqlCheck="""select * from sqlite_master where name like 'pycadent'"""
        _table=self.makeSelect(_sqlCheck).fetchone()
        if _table is None:
            _sqlCreation="""CREATE TABLE pycadent(
                    pycad_id INTEGER PRIMARY KEY,
                    pycad_entity_id INTEGER,
                    pycad_object_type TEXT,
                    pycad_object_definition TEXT,
                    pycad_style_id INTEGER,
                    pycad_security_id INTEGER,
                    pycad_undo_id INTEGER,
                    pycad_entity_state TEXT,
                    pycad_date NUMERIC,
                    pycad_visible INTEGER,
                    pycad_undo_visible INTEGER,
                    pycad_locked INTEGER,
                    pycad_bbox_xmin REAL,
                    pycad_bbox_ymin REAL,
                    pycad_bbox_xmax REAL,
                    pycad_bbox_ymax REAL)"""
            self.makeUpdateInsert(_sqlCreation)
            
    def saveEntity(self,entityObj,undoId):
        """
            this method save the entity in the db
            entityObj = object that we whant to store
        """
        _entityId=entityObj.getId()
        _entityDump=cPickle.dumps(entityObj.getConstructionPoint())
        _entityType=entityObj.getEntityType()
        _styleId=entityObj.getStyle().getId()
        _xMin,_yMin,_xMax,_yMax=entityObj.getBBox()
        _sqlInsert="""INSERT INTO pycadent (
                    pycad_entity_id,
                    pycad_object_type,
                    pycad_object_definition,
                    pycad_style_id,
                    pycad_undo_id,
                    pycad_undo_visible,
                    pycad_bbox_xmin,
                    pycad_bbox_ymin,
                    pycad_bbox_xmax,
                    pycad_bbox_ymax) VALUES
                    (%s,"%s","%s",%s,%s,1,"%s","%s",%s,%s)"""%(
                    str(_entityId),
                    str(_entityType),
                    str(_entityDump),
                    str(_styleId),
                    str(undoId),
                    str(_xMin),
                    str(_yMin),
                    str(_xMax),
                    str(_yMax))
        self.makeUpdateInsert(_sqlInsert)
        
    def getEntity(self,entityTableId):
        """
            Get the entity object from the database Univoc id
        """
        _outObj=None
        _sqlGet="""SELECT   pycad_entity_id,
                            pycad_object_type,
                            pycad_object_definition,
                            pycad_style_id
                FROM pycadent
                WHERE pycad_id=%s"""%str(entityTableId)
        _rows=self.makeSelect(_sqlGet)
        if _rows is not None:
            _dbEntRow=_rows.fetchone()
            if _dbEntRow is not None:
                _style=str(_dbEntRow[3])
                _dumpObj=cPickle.loads(str(_dbEntRow[2]))
                _outObj=PyCadEnt(_dbEntRow[1],_dumpObj,_style,_dbEntRow[0])
        return _outObj
    
    def getEntitys(self,entityId):
        """
            get all the entity with the entity id
            remarcs:
            this method return all the history of the entity
        """
        _outObj={}
        _sqlGet="""SELECT   pycad_id,
                            pycad_entity_id,
                            pycad_object_type,
                            pycad_object_definition,
                            pycad_style_id
                FROM pycadent
                WHERE pycad_entity_id=%s ORDER BY pycad_id"""%str(entityId)
        _dbEntRow=self.makeSelect(_sqlGet)
        if _dbEntRow is not None:
            for _row in _dbEntRow: 
                _style=str(_row[4])
                _dumpObj=cPickle.loads(str(_row[3]))
                _outObj[_row[0]]=PyCadEnt(_row[2],_dumpObj,_style,_row[1])
        return _outObj

    def getEntitysFromStyle(self,styleId):
        """
            return all the entity that match the styleId
        """
        _outObj={}
        _sqlGet="""SELECT   pycad_id,
                            pycad_entity_id,
                            pycad_object_type,
                            pycad_object_definition,
                            pycad_style_id
                FROM pycadent
                WHERE pycad_style_id=%s ORDER BY pycad_id"""%str(styleId)
        _dbEntRow=self.makeSelect(_sqlCheck)
        for _row in _dbEntRow: 
            _style=_row[4]
            _dumpObj=cPickle.loads(_row[3])
            _outObj[_row[0]]=PyCadEnt(_row[2],_dumpObj,_style,_row[1])
        return _outObj
    
    def getNewEntId(self):
        """
            get the last id entity 
        """
        _outObj=0
        _sqlSelect="""select max(pycad_entity_id) from pycadent"""
        _rows=self.makeSelect(_sqlSelect)
        if _rows is not None:
            _dbEntRow=_rows.fetchone()
            if _dbEntRow is not None:
                if _dbEntRow[0] is not None:
                    _outObj=int(_dbEntRow[0])
        return _outObj

    def markUndoVisibility(self,undoId,visible):
        """
            set as undo visible all the entity with undoId
        """
        _sqlVisible="""UPDATE pycadent SET pycad_undo_visible=%s
                    WHERE pycad_undo_id=%s"""%(str(visible),str(undoId))
        self.makeUpdateInsert(_sqlVisible)

    def markEntVisibility(self,entId,visible):
        """
            mark the visibility of the entity
        """
        _tableId="""SELECT MAX(pycad_id) FROM pycadent 
                    WHERE pycad_entity_id=%s"""%str(entId)
        _entId=self.fetchOneRow(_tableId)
        if _entId is None:
            raise EmptyDbSelect, "Unable to find the entity with id %s"%str(entId)
        # Update the entity state
        _sqlVisible="""UPDATE pycadent SET pycad_undo_visible=%s
                    WHERE pycad_id=%s"""%(str(visible),str(_entId))
        self.makeUpdateInsert(_sqlVisible) 
             
    def hideAllEntityIstance(self,entId,visible):
        """
            hide all the row with entId
        """
        _sqlVisible="""UPDATE pycadent SET pycad_undo_visible=%s
                    WHERE pycad_entity_id=%s"""%(str(visible),str(_entId))
        self.makeUpdateInsert(_sqlVisible)      
        
    def delete(self,entityObj):
        """
            delete the entity from db
        """
        _entityId=entityObj.getId()
        if len(self.getEntitys(_entityId)) <=0:
            raise EntDb, "The entity with id %s dose not exsist"%str(_entityId)
        _sqlDelete="""DELETE FROM pycadent 
            WHERE pycad_entity_id='%s'"""%str(_entityId)
        self.makeUpdateInsert(_sqlInsert)
        
        
""" TODO:
    pycad_entity_state
    it's the new way to mark the entity ..
    
    state could be ..
    ACTIVE:
        is when the entity are create or after a redoUndo
        means ready to be plotted on the screen and that can recive
        event(modification, delete, )
    
    DELETE:
        is when an entity is delete from the user ...
        in this case the entity is marked as deleted .
        en undoId is request 
"""
def test():
    print "*"*10+" Start Test"
    dbEnt=PyCadEntDb(None)
    print "pyCadEntDb Created"
    style=PyCadStyle(1)
    print "PyCadStyle Created"
    ent=PyCadEnt('POINT',{'a':10},style,1)
    print "PyCadEnt Created"
    dbEnt.saveEntity(ent,1)
    print "PyCadEnt Saved"
    obj=dbEnt.getEntity(1)
    print "getEntity [%s]"%str(obj)
    for e in dbEnt.getEntitys(1):
        print "Entity %s"%str(e)
    obj=dbEnt.getEntitysFromStyle
    for e in dbEnt.getEntitys(1):
        print "Entity Style %s"%str(e)
    _newId=dbEnt.getNewEntId()
    print "New id %i"%(_newId)

    #to be tested 
    #markUndoVisibility
    #delete