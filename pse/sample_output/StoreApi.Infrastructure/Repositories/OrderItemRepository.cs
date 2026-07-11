using System;
using System.Collections.Generic;
using System.Linq;
using StoreApi.Domain.Entities;
using StoreApi.Domain.Repositories;

namespace StoreApi.Infrastructure.Repositories;

public class OrderItemRepository : IOrderItemRepository
{
    private readonly List<OrderItem> _items = new();

    public IEnumerable<OrderItem> GetAll()
    {
        return _items;
    }

    public OrderItem? GetById(Guid id)
    {
        return _items.FirstOrDefault(entity =>
            EqualityComparer<Guid>.Default.Equals(entity.ProductId, id));
    }

    public void Create(OrderItem entity)
    {
        if (GetById(entity.ProductId) is not null)
        {
            Update(entity);
            return;
        }

        _items.Add(entity);
    }

    public void Update(OrderItem entity)
    {
        var index = _items.FindIndex(existing =>
            EqualityComparer<Guid>.Default.Equals(existing.ProductId, entity.ProductId));

        if (index >= 0)
        {
            _items[index] = entity;
            return;
        }

        _items.Add(entity);
    }

    public void Delete(Guid id)
    {
        var entity = GetById(id);
        if (entity is not null)
        {
            _items.Remove(entity);
        }
    }
}
