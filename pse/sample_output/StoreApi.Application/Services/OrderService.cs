using System.Collections.Generic;
using StoreApi.Domain.Entities;
using StoreApi.Domain.Repositories;
using StoreApi.Application.Interfaces;

namespace StoreApi.Application.Services;

public class OrderService : IOrderService
{
    private readonly IOrderRepository _repository;

    public OrderService(IOrderRepository repository)
    {
        _repository = repository;
    }

    public IEnumerable<Order> GetAll()
    {
        return _repository.GetAll();
    }

    public Order? GetById(Guid id)
    {
        return _repository.GetById(id);
    }

    public Order Create(Order entity)
    {
        _repository.Create(entity);
        return entity;
    }

    public bool Update(Guid id, Order entity)
    {
        if (_repository.GetById(id) is null)
        {
            return false;
        }

        entity.Id = id;
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
