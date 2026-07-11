using System.Collections.Generic;
using StoreApi.Domain.Entities;

namespace StoreApi.Application.Interfaces;

public interface IOrderItemService
{
    IEnumerable<OrderItem> GetAll();

    OrderItem? GetById(Guid id);

    OrderItem Create(OrderItem entity);

    bool Update(Guid id, OrderItem entity);

    bool Delete(Guid id);
}
