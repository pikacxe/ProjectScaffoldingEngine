using System.Collections.Generic;
using System.Linq;
using Microsoft.EntityFrameworkCore;
using StoreApi.Domain.Entities;
using StoreApi.Domain.Repositories;
using StoreApi.Infrastructure.Persistence;

namespace StoreApi.Infrastructure.Repositories;

public class OrderItemRepository : IOrderItemRepository
{
    private readonly AppDbContext _dbContext;
    private readonly DbSet<OrderItem> _entities;

    public OrderItemRepository(AppDbContext dbContext)
    {
        _dbContext = dbContext;
        _entities = dbContext.Set<OrderItem>();
    }

    public IEnumerable<OrderItem> GetAll()
    {
        return _entities.AsNoTracking().ToList();
    }

    public OrderItem? GetById(Guid id)
    {
        return _entities.Find(id);
    }

    public void Create(OrderItem entity)
    {
        _entities.Add(entity);
        _dbContext.SaveChanges();
    }

    public void Update(OrderItem entity)
    {
        _entities.Update(entity);
        _dbContext.SaveChanges();
    }

    public void Delete(Guid id)
    {
        var entity = _entities.Find(id);
        if (entity is null)
        {
            return;
        }

        _entities.Remove(entity);
        _dbContext.SaveChanges();
    }
}
