using System.Collections.Generic;
using System.Linq;
using Microsoft.EntityFrameworkCore;
using StoreApi.Domain.Entities;
using StoreApi.Domain.Repositories;
using StoreApi.Infrastructure.Persistence;

namespace StoreApi.Infrastructure.Repositories;

public class OrderRepository : IOrderRepository
{
    private readonly AppDbContext _dbContext;
    private readonly DbSet<Order> _entities;

    public OrderRepository(AppDbContext dbContext)
    {
        _dbContext = dbContext;
        _entities = dbContext.Set<Order>();
    }

    public IEnumerable<Order> GetAll()
    {
        return _entities.AsNoTracking().ToList();
    }

    public Order? GetById(Guid id)
    {
        return _entities.Find(id);
    }

    public void Create(Order entity)
    {
        _entities.Add(entity);
        _dbContext.SaveChanges();
    }

    public void Update(Order entity)
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
