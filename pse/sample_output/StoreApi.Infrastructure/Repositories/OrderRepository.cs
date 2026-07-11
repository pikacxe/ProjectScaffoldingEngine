using System;
using System.Collections.Generic;
using System.Linq;
using StoreApi.Domain.Entities;
using StoreApi.Domain.Repositories;

namespace StoreApi.Infrastructure.Repositories;

public class OrderRepository : IOrderRepository
{
    private readonly List<Order> _items = new();

    public IEnumerable<Order> GetAll()
    {
        return _items;
    }

    public Order? GetById(Guid id)
    {
        return _items.FirstOrDefault(entity =>
            EqualityComparer<Guid>.Default.Equals(entity.Id, id));
    }

    public void Create(Order entity)
    {
        if (GetById(entity.Id) is not null)
        {
            Update(entity);
            return;
        }

        _items.Add(entity);
    }

    public void Update(Order entity)
    {
        var index = _items.FindIndex(existing =>
            EqualityComparer<Guid>.Default.Equals(existing.Id, entity.Id));

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
