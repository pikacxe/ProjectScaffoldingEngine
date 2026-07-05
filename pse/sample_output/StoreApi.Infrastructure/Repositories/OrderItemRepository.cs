using System;
using System.Collections.Generic;
using StoreApi.Domain.Entities;
using StoreApi.Domain.Repositories;

namespace StoreApi.Infrastructure.Repositories;

public class OrderItemRepository : IOrderItemRepository
{
    public IEnumerable<OrderItem> GetAll()
    {
        return Array.Empty<OrderItem>();
    }

    public OrderItem? GetById(Guid id)
    {
        return null;
    }

    public void Create(OrderItem entity)
    {
        throw new NotImplementedException();
    }

    public void Update(OrderItem entity)
    {
        throw new NotImplementedException();
    }

    public void Delete(Guid id)
    {
        throw new NotImplementedException();
    }
}