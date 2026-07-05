using System.Collections.Generic;
using StoreApi.Domain.Entities;

namespace StoreApi.Domain.Repositories;

public interface IOrderRepository
{
    IEnumerable<Order> GetAll();

    Order? GetById(Guid id);

    void Create(Order entity);

    void Update(Order entity);

    void Delete(Guid id);
}