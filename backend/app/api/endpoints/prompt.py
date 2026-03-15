"""
提示词 API
Prompt API
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.prompt import Prompt

router = APIRouter()


class PromptCreate(BaseModel):
    name: str = Field(..., description="提示词名称")
    description: Optional[str] = Field(None, description="提示词描述")
    content: str = Field(..., description="提示词内容")
    category: str = Field(default="用户分享", description="分类：官方示例/用户分享")
    is_official: bool = Field(default=False, description="是否官方")


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    is_official: Optional[bool] = None


class PromptResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    content: str
    category: str
    is_official: bool
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("", response_model=List[PromptResponse])
async def get_prompts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = Query(None, description="按分类筛选"),
    is_official: Optional[bool] = Query(None, description="按官方筛选"),
    db: Session = Depends(get_db)
):
    """
    获取提示词列表
    """
    query = db.query(Prompt)
    
    if category:
        query = query.filter(Prompt.category == category)
    if is_official is not None:
        query = query.filter(Prompt.is_official == is_official)
    
    prompts = query.order_by(Prompt.is_official.desc(), Prompt.id.desc()).offset(skip).limit(limit).all()
    
    return [
        PromptResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            content=p.content,
            category=p.category,
            is_official=p.is_official,
            created_at=p.created_at.isoformat() if p.created_at else "",
            updated_at=p.updated_at.isoformat() if p.updated_at else None
        )
        for p in prompts
    ]


@router.post("", response_model=PromptResponse)
async def create_prompt(
    prompt: PromptCreate,
    db: Session = Depends(get_db)
):
    """
    创建提示词
    """
    db_prompt = Prompt(
        name=prompt.name,
        description=prompt.description,
        content=prompt.content,
        category=prompt.category,
        is_official=prompt.is_official
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    
    return PromptResponse(
        id=db_prompt.id,
        name=db_prompt.name,
        description=db_prompt.description,
        content=db_prompt.content,
        category=db_prompt.category,
        is_official=db_prompt.is_official,
        created_at=db_prompt.created_at.isoformat() if db_prompt.created_at else "",
        updated_at=db_prompt.updated_at.isoformat() if db_prompt.updated_at else None
    )


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个提示词
    """
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    
    return PromptResponse(
        id=prompt.id,
        name=prompt.name,
        description=prompt.description,
        content=prompt.content,
        category=prompt.category,
        is_official=prompt.is_official,
        created_at=prompt.created_at.isoformat() if prompt.created_at else "",
        updated_at=prompt.updated_at.isoformat() if prompt.updated_at else None
    )


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: int,
    prompt: PromptUpdate,
    db: Session = Depends(get_db)
):
    """
    更新提示词
    """
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    
    update_data = prompt.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prompt, key, value)
    
    db.commit()
    db.refresh(db_prompt)
    
    return PromptResponse(
        id=db_prompt.id,
        name=db_prompt.name,
        description=db_prompt.description,
        content=db_prompt.content,
        category=db_prompt.category,
        is_official=db_prompt.is_official,
        created_at=db_prompt.created_at.isoformat() if db_prompt.created_at else "",
        updated_at=db_prompt.updated_at.isoformat() if db_prompt.updated_at else None
    )


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """
    删除提示词
    """
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    
    db.delete(prompt)
    db.commit()
    
    return {"success": True, "message": "删除成功"}
