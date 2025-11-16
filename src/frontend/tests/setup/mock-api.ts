/**
 * Mock API responses for testing without requiring localhost:8000
 * This allows tests to run independently of the backend server
 */

import { test as base } from '@playwright/test';

// Mock API responses
const mockPolyhedra = [
  {
    symbol: 'A',
    name: 'Triangle',
    classification: 'primitive',
    sides: 3,
    vertices: [[1, 0, 0], [-0.5, 0.866, 0], [-0.5, -0.866, 0]],
    compression_ratio: 500
  },
  {
    symbol: 'B',
    name: 'Square',
    classification: 'primitive',
    sides: 4,
    vertices: [[0.5, 0.5, 0], [-0.5, 0.5, 0], [-0.5, -0.5, 0], [0.5, -0.5, 0]],
    compression_ratio: 500
  },
  {
    symbol: 'C',
    name: 'Pentagon',
    classification: 'primitive',
    sides: 5,
    vertices: [[0, 1, 0], [0.951, 0.309, 0], [0.588, -0.809, 0], [-0.588, -0.809, 0], [-0.951, 0.309, 0]],
    compression_ratio: 500
  }
];

const mockGeneratedPolyform = {
  success: true,
  symbol: 'AB',
  unicode: 'α',
  composition: 'AB',
  geometry: {
    lod: {
      full: {
        vertices: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [2, 0, 0], [3, 0, 0], [3, 1, 0], [2, 1, 0]],
        indices: [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7],
        normals: []
      }
    }
  },
  metadata: {
    polygon_count: 2,
    edge_count: 6,
    stability: 0.85,
    composition: 'AB'
  },
  compressionRatio: 250
};

export const test = base.extend({
  page: async ({ page }, use) => {
    // Intercept API calls and return mock data
    await page.route('**/tier1/polyhedra**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPolyhedra)
      });
    });

    await page.route('**/api/polyform/generate**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockGeneratedPolyform)
      });
    });

    await page.route('**/api/polyform/decode**', async route => {
      const request = route.request();
      const postData = request.postDataJSON();
      const encoding = postData?.encoding || 'A';
      
      const mockGeometry = {
        lod: {
          full: {
            vertices: mockPolyhedra.find(p => p.symbol === encoding)?.vertices || mockPolyhedra[0].vertices,
            indices: [],
            normals: []
          }
        },
        metadata: {
          polygon_count: 1,
          edge_count: mockPolyhedra.find(p => p.symbol === encoding)?.sides || 3
        }
      };

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockGeometry)
      });
    });

    await page.route('**/api/attachment/sequence**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          stability: 0.85,
          fold_angle: 90.0,
          steps: []
        })
      });
    });

    await page.route('**/health**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'healthy' })
      });
    });

    await use(page);
  },
});

export { expect } from '@playwright/test';

