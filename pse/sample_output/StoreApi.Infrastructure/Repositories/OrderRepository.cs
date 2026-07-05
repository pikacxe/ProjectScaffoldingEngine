using System;
using System.Collections.Generic;
using StoreApi.Domain.Entities;
using StoreApi.Domain.Repositories;

namespace StoreApi.Infrastructure.Repositories;

public class OrderRepository : IOrderRepository
{
    public IEnumerable<Order> GetAll()
    {
        return Array.Empty<Order>();
    }

    public Order? GetById(Guid id)
    {
        return null;
    }

    public void Create(Order entity)
    {
        throw new NotImplementedException();
    }

    public void Update(Order entity)
    {
        throw new NotImplementedException();
    }

    public void Delete(Guid id)
    {
        throw new NotImplementedException();
    }
}