using System.Collections.Generic;
using StoreApi.Domain.Entities;

namespace StoreApi.Domain.Repositories;

public interface IOrderItemRepository
{
    IEnumerable<OrderItem> GetAll();

    OrderItem? GetById(Guid id);

    void Create(OrderItem entity);

    void Update(OrderItem entity);

    void Delete(Guid id);
}