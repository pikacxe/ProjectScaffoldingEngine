using System;
using System.Collections.Generic;
using StoreApi.Domain.Entities;
using StoreApi.Domain.Repositories;

namespace StoreApi.Infrastructure.Repositories;

public class UserRepository : IUserRepository
{
    public IEnumerable<User> GetAll()
    {
        return Array.Empty<User>();
    }

    public User? GetById(Guid id)
    {
        return null;
    }

    public void Create(User entity)
    {
        throw new NotImplementedException();
    }

    public void Update(User entity)
    {
        throw new NotImplementedException();
    }

    public void Delete(Guid id)
    {
        throw new NotImplementedException();
    }
}