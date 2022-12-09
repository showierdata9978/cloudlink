from dataclasses import dataclass
import uuid
from typing import Any

@dataclass
class Disk:
    contents: Any
    owner_id: str
    _id: str



class CloudDisk:
    def __init__(self, CloudAccount):
        self.CA = CloudAccount
        self.cl = self.CA.cloudlink
        self.db = self.CA.home_server.db.cl_homeserver

        self.cl.supporter.codes.update({
            "ToManyDisks": ("E", 114, "To Many Disks")
        })

    async def create_disk(self, client, message, listener):
        if not 'val' in message:
            await self.cloudlink.send_code(client, "Syntax", extra_data={"key":"val"}, listener=listener)
            return

        if type(message['val']) in [dict, list]:
            await self.cloudlink.send_code(client, "DataType", extra_data={"key":"val"}, listener=listener)
            return

        if not self.CA.isAuthed(client):
            await self.cl.send_code(client, "Refused", extra_data={"error":"noAuth"} ,listener=listener)
            return
        

        disks = self.db.disks.find({"owner_id":client.session.account._id})

        count = 0
        if disks is not None:
          for _ in disks:
            count += 1

        if count > 10:
            await self.cl.send_code(client, "ToManyDisks", listener=listener)
            return
        
        if len(message['val']) > ((8*1000)*10): 
            # 10kb
            await self.cl.send_code(client, "TooLarge", listener=listener)
            return
        id = uuid.uuid4().hex
        self.db.disks.insert_one({"_id":id, "contents": message['val'], "owner_id": client.session.account._id})
    
        await self.cl.send_code(client, "OK", listener=listener, extra_data={"diskid": id })
        
    async def delete_disk(self, client, message, listener):
        if not 'diskid' in message:
            await self.cloudlink.send_code(client, "Syntax", extra_data={"key":"diskid"}, listener=listener)
            return
        

        if not self.CA.isAuthed(client):
            await self.cl.send_code(client, "Refused", extra_data={"error":"noAuth"} ,listener=listener)
            return
        
        if not self.db.disks.find_one({"_id": message['diskid'], "owner_id": client.session.account._id}):
            await self.cl.send_code(client, "IDNotFound", listener=listener)
            return

        self.db.disks.delete_one({"_id": message['diskid'], "owner_id": client.session.account._id})
        await self.cl.send_code(client, "OK", listener=listener)
    
    async def update_disk(self, client, message, listener):
        if not 'diskid' in message:
            await self.cloudlink.send_code(client, "Syntax", extra_data={"key":"diskid"}, listener=listener)
            return
        
        if not 'val' in message:
            await self.cloudlink.send_code(client, "Syntax", extra_data={"key":"val"}, listener=listener)
            return
        
        if type(message['val']) in [dict, list]:
            await self.cloudlink.send_code(client, "DataType", extra_data={"key":"val"}, listener=listener)
            return

        if not self.CA.isAuthed(client):
            await self.cl.send_code(client, "Refused", extra_data={"error":"noAuth"} ,listener=listener)
            return
        
        if not self.db.disks.find_one({"_id": message['diskid'], "owner_id": client.session.account._id}):
            await self.cl.send_code(client, "IDNotFound", listener=listener)
            return

        self.db.disks.update_one({"_id": message['diskid'], "owner_id": client.session.account._id}, {
            "$set":{
                "contents": message['val']
            }
        })

        await self.cl.send_code(client, "OK", listener=listener)
    
    async def get_disk(self, client, message, listener):
        if not 'diskid' in message:
            await self.cloudlink.send_code(client, "Syntax", extra_data={"key":"diskid"}, listener=listener)
            return
        
        if not self.CA.isAuthed(client):
            await self.cl.send_code(client, "Refused", extra_data={"error":"noAuth"} ,listener=listener)
            return
        disk = self.db.disks.find_one({"_id": message['diskid'], "owner_id": client.session.account._id})
        if not disk:
            await self.cl.send_code(client, "IDNotFound", listener=listener)
            return

        await self.cl.send_code(client, "OK", extra_data={"val":disk['contents']}, listener=listener)


        
