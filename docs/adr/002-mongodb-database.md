# ADR-002: Use MongoDB as Primary Database

**Status:** Accepted

**Date:** 2023 (Initial project setup)

**Deciders:** Project team

---

## Context

We needed a database solution for storing user data and todo items with these requirements:

- Flexible schema for rapid iteration
- Good performance for document-based queries
- Horizontal scaling capability
- Cloud hosting options (Atlas)
- JSON-like data structures

### Alternatives Considered

1. **PostgreSQL**
   - Pros: ACID compliance, mature, excellent for relational data, JSON support
   - Cons: Rigid schema, more complex for simple document storage

2. **MySQL/MariaDB**
   - Pros: Mature, widely supported, good performance
   - Cons: Less flexible schema, not optimized for document storage

3. **MongoDB** ✅
   - Pros: Flexible schema, document-oriented, cloud-native (Atlas), native JSON
   - Cons: Different query paradigm, eventual consistency in some configs

4. **DynamoDB**
   - Pros: AWS-managed, highly scalable
   - Cons: Vendor lock-in, complex pricing, limited query capabilities

---

## Decision

We chose **MongoDB** as our primary database, accessed via **pymongo** driver.

### Rationale

1. **Learning Opportunity**: Chosen as a learning exercise (team more familiar with PostgreSQL)
2. **Document Model**: Natural fit for todo items (title, description, metadata)
3. **Schema Flexibility**: Can evolve data model without migrations
4. **MongoDB Atlas**: Free tier for development, easy production scaling
5. **JSON Native**: Seamless integration with FastAPI/Pydantic
6. **Cloud-First**: Atlas provides managed hosting, backups, monitoring

### Implementation Details

- **Driver**: `pymongo` 4.6.3 (synchronous, initial learning choice)
  - **Note**: This was a first approach - Motor (async) should be considered for production (see Technical Debt)
- **Connection**: Single client instance, connection pooling handled by pymongo
- **Collections**: `users` and `todos` (separate for clear separation)
- **IDs**: MongoDB ObjectId (custom Pydantic type `PyObjectId` for validation)

---

## Consequences

### Positive

✅ **Rapid Development**: No schema migrations during early iterations  
✅ **Cloud Deployment**: MongoDB Atlas free tier for dev/testing  
✅ **Flexible Data**: Easy to add fields without ALTER TABLE  
✅ **JSON Alignment**: Direct mapping between API models and DB documents  
✅ **Horizontal Scaling**: Sharding available when needed  

### Negative

⚠️ **No Transactions**: Limited multi-document transactions (not needed yet)  
⚠️ **Query Complexity**: Have to learn MongoDB query language  
⚠️ **Eventual Consistency**: Possible in replica sets (acceptable for todos)  
⚠️ **No Joins**: Requires denormalization or multiple queries  

### Technical Debt

- **pymongo → Motor Migration** (Important: addresses initial learning approach)
  - Current: Synchronous `pymongo` used as first learning choice
  - Future: Async Motor driver for true async/await performance
  - Impact: Better concurrency, non-blocking I/O, FastAPI async benefits
  - Effort: Moderate (change driver, update all DB calls to async)
- Limited indexing strategy (no indexes defined - performance optimization needed)
- No connection retry logic for transient failures
- Collection names in environment variables (could be hardcoded)

---

## Follow-up Decisions

- **Custom PyObjectId Type** (in `app/models/base.py`): Created Pydantic type for MongoDB ObjectIds
- **User Isolation**: Every todo has `user_id` field for data separation
- **Motor Migration (Recommended)**: Upgrade from pymongo to Motor for async operations
  - Current synchronous approach was initial learning choice
  - Motor would provide true async/await with FastAPI
  - Significant performance improvement for concurrent requests

---

## References

- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB Best Practices](https://www.mongodb.com/docs/manual/administration/production-notes/)
- [app/database/mongodb.py](file:///root/projects/to-do/app/database/mongodb.py) - Connection implementation
- [app/models/base.py](file:///root/projects/to-do/app/models/base.py) - PyObjectId custom type
