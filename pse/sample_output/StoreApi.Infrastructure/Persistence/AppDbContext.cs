using Microsoft.EntityFrameworkCore;
using StoreApi.Domain.Entities;

namespace StoreApi.Infrastructure.Persistence;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options)
        : base(options)
    {
    }

    public DbSet<Order> OrderSet => Set<Order>();
    public DbSet<OrderItem> OrderItemSet => Set<OrderItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Order>().HasKey(entity => entity.Id);
        modelBuilder.Entity<OrderItem>().HasKey(entity => entity.ProductId);
    }
}
