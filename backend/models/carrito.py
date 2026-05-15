from sqlalchemy import Column, ForeignKey, Integer

from database import Base


class CarritoItem(Base):
    __tablename__ = "carrito_items"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False, index=True)
    cantidad = Column(Integer, default=1, nullable=False)
