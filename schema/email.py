from pydantic import EmailStr, BaseModel


class EmailSchema(BaseModel):
    email: EmailStr
