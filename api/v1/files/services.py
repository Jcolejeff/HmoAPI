import os
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from typing import List
from api.v1.files.models import File
from api.v1.files.schemas import UploadFileSchema
from api.core.base.services import Service
from decouple import config
from sqlalchemy.sql import and_
from PIL import Image


UPLOAD_DIR = "filestorage"
IMAGE_BASE_DIR = "images"
FILE_EXTENSION_BLACKLIST = config("FILE_EXT_BLACKLIST", default=[".exe", ".bat", ".sh", ".env"])

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


class FileService(Service):

    def __init__(self) -> None:
        pass


    @classmethod
    async def create(cls, files: List[UploadFile], created_by: int, payload: UploadFileSchema, db: Session):

        ##TODO:
        ##check file size of file before upload using tiangolo strategy at https://github.com/tiangolo/fastapi/issues/362. change file write to async as well

        for file in files:

            # ensure file has a valid extension
            file_ext = os.path.splitext(file.filename)[-1]
            if ((not file_ext) or len(os.path.splitext(file.filename)[-1]) < 4 or file_ext in FILE_EXTENSION_BLACKLIST):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot upload File type!")

            # Create the base folder + all other folders
            save_path = os.path.join(str(payload.organization_id), payload.entity_name.value, str(payload.entity_id)) 

            if cls.isImage(file):
                storage_path = os.path.join(UPLOAD_DIR, IMAGE_BASE_DIR, save_path)
            else:
                storage_path = os.path.join(UPLOAD_DIR, save_path)

            try:
                os.makedirs(storage_path, exist_ok=True)
            except:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating base folders")

            #rename file and save as jpg if image
            if await cls.isImage(file):
                file_ext = ".jpg"

            file.filename = str(uuid4().hex + file_ext)
            
            full_write_path = os.path.realpath(os.path.join(storage_path, file.filename))

            # write file contents
            contents = await file.read()
            try:
                with open(full_write_path, "wb") as f:
                    f.write(contents)
            except OSError as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error writing to the file")

            # Retrieve the file size
            filesize = os.path.getsize(full_write_path)

            url = await cls.create_file_url(file_name=file.filename, payload=payload)

            file = File(
                file_name=file.filename,
                file_path=os.path.join(save_path, file.filename),
                entity_name=payload.entity_name.value,
                entity_id=payload.entity_id,
                file_size=filesize,
                organization_id=payload.organization_id,
                created_by=created_by,
                url=url,
            )

            db.add(file)
            db.commit()

        return "Success"

    @classmethod
    async def get(cls, url: str, size: str, db: Session):
        try:
            organization_id, entity_name, entity_id, file_name = url.split("/")
        except Exception as ex:
            print(ex)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid Url.")
            
        file = db.query(File).filter(and_(File.entity_name==entity_name, 
                                          File.organization_id==organization_id,
                                          File.entity_id==entity_id,
                                          File.file_name==file_name)).first()
        if not file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

        file_ext = os.path.splitext(file.file_name)[-1]
        if file_ext not in [".jpg", '.jpeg', '.png']:
           full_path = os.path.realpath(os.path.join(UPLOAD_DIR, file.file_path))
        else:
            if size:
                size = size.split("x")
                width, height = size[0].strip(), size[1].strip()
                size_path = str(width)+'_'+str(height)
                last_index = file.file_path.rindex('/')
                path_without_name = file.file_path[:last_index]
                original_image_path = os.path.realpath(os.path.join(UPLOAD_DIR, IMAGE_BASE_DIR, file.file_path))

                if not os.path.exists(os.path.realpath(os.path.join(UPLOAD_DIR, IMAGE_BASE_DIR, path_without_name, size_path,file.file_name))):
                    save_path = os.path.join(UPLOAD_DIR, IMAGE_BASE_DIR, path_without_name, size_path)
                    os.makedirs(save_path,exist_ok=True)
                    full_path = await cls.resize_image(full_path=original_image_path, save_path = save_path,
                                                        width=width, height=height)
                else:
                    full_path = os.path.realpath(os.path.join(UPLOAD_DIR, IMAGE_BASE_DIR, path_without_name, size_path,file.file_name))
                                 
            else:
                full_path = os.path.realpath(os.path.join(UPLOAD_DIR, IMAGE_BASE_DIR, file.file_path))
        
        return full_path

    @classmethod
    async def update(cls):
        pass

    @classmethod
    async def delete(cls):
        pass

    @classmethod     
    async def isImage(cls, file):
        if "image/" in file.content_type:
            return True
        else:
            return False


    @classmethod     
    async def create_file_url(cls, file_name: str, payload: UploadFileSchema):
        url = f"/{payload.organization_id}/{payload.entity_name.value}/{payload.entity_id}/{file_name}"
        return url

    @classmethod
    async def resize_image(cls, full_path: str, save_path: str, width: int, height: int, crop_type="middle"):

        img = Image.open(full_path)

        # dimensions must be an integer value
        width = int(width if str(width).isdigit() else 100)
        height = int(height if str(height).isdigit() else 100)

        # use image dimension for any dimension not set
        width = width if width else img.size[0]
        height = height if height else img.size[1]

        # dimensions should not go below 50
        width = width if width > 50 else 100
        height = height if height > 50 else 100

        # dimensions should not exceed image size
        width = width if width < img.size[0] else img.size[0]
        height = height if height < img.size[1] else img.size[1]

        # img = await cls.crop(img, width, height, crop_type)
        img = img.resize(size=(width, height))
        img = img.convert('RGB')
        save_path = os.path.join(save_path, full_path.split("/")[-1])

        img.save(save_path, quality=95)
        
        img.close()

        return save_path


    @classmethod
    async def crop(cls, image, width, height, crop_type="middle"):
        # If height is higher we resize vertically, if not we resize horizontally
        img = image
        size = (width, height)
        # Get current and desired ratio for the images
        img_ratio = img.size[0] / float(img.size[1])
        ratio = size[0] / float(size[1])
        #The image is scaled/cropped vertically or horizontally depending on the ratio
        if ratio > img_ratio:
            img = img.resize((size[0], int(round(size[0] * img.size[1] / img.size[0]))))
            # Crop in the top, middle or bottom
            if crop_type == 'top':
                box = (0, 0, img.size[0], size[1])
            elif crop_type == 'middle':
                box = (0, int(round((img.size[1] - size[1]) / 2)), img.size[0],
                    int(round((img.size[1] + size[1]) / 2)))
            elif crop_type == 'bottom':
                box = (0, img.size[1] - size[1], img.size[0], img.size[1])
            else :
                raise ValueError('ERROR: invalid value for crop_type')
            img = img.crop(box)
        elif ratio < img_ratio:
            img = img.resize((int(round(size[1] * img.size[0] / img.size[1])), size[1]))
            # Crop in the top, middle or bottom
            if crop_type == 'top':
                box = (0, 0, size[0], img.size[1])
            elif crop_type == 'middle':
                box = (int(round((img.size[0] - size[0]) / 2)), 0,
                    int(round((img.size[0] + size[0]) / 2)), img.size[1])
            elif crop_type == 'bottom':
                box = (img.size[0] - size[0], 0, img.size[0], img.size[1])
            else :
                raise ValueError('ERROR: invalid value for crop_type')
            img = img.crop(box)
        else :
            img = img.resize((size[0], size[1]))
        # If the scale is the same, we do not need to crop
        return img



