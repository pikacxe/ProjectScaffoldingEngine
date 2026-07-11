using System.Collections.Generic;
using StoreApi.Domain.Entities;
using StoreApi.Domain.Repositories;
using StoreApi.Application.Interfaces;

namespace StoreApi.Application.Services;

public class OrderItemService : IOrderItemService
{
    private readonly IOrderItemRepository _repository;

    public OrderItemService(IOrderItemRepository repository)
    {
        _repository = repository;
    }

    public IEnumerable<OrderItem> GetAll()
    {
        return _repository.GetAll();
    }

    public OrderItem? GetById(Guid id)
    {
        return _repository.GetById(id);
    }

    public OrderItem Create(OrderItem entity)
    {
        _repository.Create(entity);
        return entity;
    }

    public bool Update(Guid id, OrderItem entity)
    {
        if (_repository.GetById(id) is null)
        {
            return false;
        }

        entity.ProductId = id;
        _repository.Update(entity);
        return true;
    }

    public bool Delete(Guid id)
    {
        if (_repository.GetById(id) is null)
        {
            return false;
        }

        _repository.Delete(id);
        return true;
    }
}
