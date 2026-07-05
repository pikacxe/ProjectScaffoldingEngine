using System.Collections.Generic;
using StoreApi.Domain.Entities;

namespace StoreApi.Domain.Repositories;

public interface IUserRepository
{
    IEnumerable<User> GetAll();

    User? GetById(Guid id);

    void Create(User entity);

    void Update(User entity);

    void Delete(Guid id);
}