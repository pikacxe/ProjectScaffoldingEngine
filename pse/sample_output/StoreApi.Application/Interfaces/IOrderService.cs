using System.Collections.Generic;
using StoreApi.Domain.Entities;

namespace StoreApi.Application.Interfaces;

public interface IOrderService
{
    IEnumerable<Order> GetAll();

    Order? GetById(Guid id);

    Order Create(Order entity);

    bool Update(Guid id, Order entity);

    bool Delete(Guid id);
}
